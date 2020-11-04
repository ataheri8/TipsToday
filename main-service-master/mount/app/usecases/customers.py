from dataclasses import asdict
import uuid
import csv
from typing import List

from pydantic import BaseModel

from app.common import logger, errors
from app.usecases.context import Context

from app.adapters import sms

from app.domain import customers, sessions, clients, card_proxies, stores
from app.domain import security as reset_sek

from app.common import security as sek
from app.common import json as json_util

from app.services import fis_client


FROM_HEADERS = ["First Name", "Last Name", "Mobile Number", "Employee ID", "Address",
                "City", "Province", "Postal Code"]


class CustomerOut(BaseModel):
    customer_id: int
    identifier: str
    first_name: str
    last_name: str
    status: str
    created_at: str
    updated_at: str
    store_ids: List[int] = []

    @staticmethod
    def from_customer(d):
        return CustomerOut(
            customer_id=d.customer_id,
            identifier=d.identifier,
            first_name=d.first_name,
            last_name=d.last_name,
            status=d.customer_status,
            created_at=d.created_at,
            updated_at=d.updated_at,
            store_ids=d.store_ids,
        )


#
# writes
#
async def create(ctx: Context, identifier, first_name, last_name, stores_data,
                 passphrase=None):
    c_repo = customers.CustomersRepo(ctx.db)
    cl_repo = clients.ClientsRepo(ctx.db)
    s_repo = stores.StoresRepo(ctx.db)
    cm_repo = customers.CustomersMappingRepo(ctx.db)

    _identifier = customers.clean_phone_number(identifier)

    # check that it is a valid phone number
    phone_number_is_valid, exc = sms.validate_number(_identifier)
    if not phone_number_is_valid:
        return False, exc

    customer_exists = await c_repo.get_by_identifier(_identifier)
    if customer_exists:
        return False, errors.E['customers_identifier_exists']

    # ensure that the client and store exist
    _store_ids = [s.store_id for s in stores_data]
    stores_exist, stores_not_exist = await check_stores_exist(ctx, _store_ids)
    if stores_not_exist:
        return False, errors.E['customers_invalid_store_id']

    client_id = stores_exist[0]['client_id']
    client_exists = await cl_repo.get_by_client_id(client_id)
    if not client_exists:
        return False, errors.E['customers_invalid_client_id']

    employee_exists, employee_not_exists = await check_employee_exists(ctx, client_id,
                                                                       stores_data)
    if employee_exists:
        return False, errors.E['customers_employee_id_exists']

    # generate a temp password
    temp_pass = sek.gen_random_password()

    cust_rec = await c_repo.create(identifier, temp_pass, first_name, last_name)
    if cust_rec:
        # map to stores, etc
        for s in stores_data:
            _mapping = await cm_repo.add_mapping(client_id, s.store_id, cust_rec['customer_id'],
                                                 s.employee_id)

        mappings = await cm_repo.get_by_customer_id(cust_rec['customer_id'])
        store_ids = [m.get('store_id') for m in mappings if mappings]
        # reset password!
        reset_start, reset_data = await start_reset_pass(ctx, _identifier)
        if not reset_start:
            return False, errors.E['customers_unable_to_initiate_pass_reset']

        return True, customers.Customer.from_record(cust_rec, store_ids=store_ids)

    else:
        return False, errors.E['customers_unable_to_create']


async def activate_card(ctx: Context, customer_id, proxy):
    c_repo = customers.CustomersRepo(ctx.db)
    a_repo = customers.AddressesRepo(ctx.db)
    p_repo = card_proxies.ClientCardProxiesRepo(ctx.db)
    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)

    c_exists = await c_repo.get_by_customer_id(customer_id)
    if not c_exists:
        return False, errors.E['customers_id_not_found']

    addy = await a_repo.get_by_customer_id(customer_id)
    if not addy:
        return False, errors.E['customers_address_missing']

    # TODO: see if there should be a customer status check here
    p_exists = await p_repo.search(only_one=True, proxy=proxy)
    if not p_exists:
        return False, errors.E['customers_proxy_not_found']

    if p_exists['proxy_status'] != card_proxies.PROXY_STATUS_AVAILABLE:
        return False, errors.E['customers_proxy_not_available']

    if c_exists['client_id'] != p_exists['client_id']:
        return False, errors.E['customers_proxy_client_mismatch']

    # assign the proxy to the customer
    # but only if they don't have an active card already
    has_card = await r_repo.search(customer_id=customer_id,
                                   proxy_status=card_proxies.CARD_STATUS_ACTIVE,)
    if has_card:
        return False, errors.E['customers_has_active_card']

    # call FIS
    fis_succeed, fis_data = await fis_client.activate_card(proxy,
                                                           c_exists['first_name'],
                                                           c_exists['last_name'],
                                                           addy[0]['city'],
                                                           addy[0]['country'])

    if not fis_succeed:
        return False, errors.E['customers_unable_to_activate_with_processor']

    # parse FIS data
    fis_parsed = fis_client.parse_pipe_response(fis_data)
    person_id = fis_parsed[1]
    last4 = fis_parsed[0][-4:]
    exp = fis_parsed[-1]

    card_proxy = await r_repo.create(customer_id, proxy, person_id,
                                     last4=last4, expiry=exp)

    if not card_proxy:
        return False, errors.E['customers_unable_to_create_proxy_db']

    # mark it as unavailable from the client
    mark_assigned = await p_repo.change_status(card_proxies.PROXY_STATUS_ASSIGNED,
                                               proxy)

    if not mark_assigned:
        return False, errors.E['customers_unable_to_mark_proxy_assigned']

    return True, card_proxies.CustomerCardProxy.from_record(card_proxy)


async def card_transfer(ctx: Context, customer_id, to_proxy, amount):
    c_repo = customers.CustomersRepo(ctx.db)
    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)

    cust_proxy = await r_repo.get_customer_active_proxy(customer_id)

    if not cust_proxy:
        return False, errors.E['customers_no_active_proxy']

    moved, moved_data = await fis_client.transfer_funds(cust_proxy['proxy'],
                                                        to_proxy,
                                                        amount)
    if not moved:
        logger.exception("FIS return for transfering funds: ", data=moved_data)
        return False, errors.E['customer_unable_to_transfer_funds']

    fis_parsed = fis_client.parse_pipe_response(moved_data)
    res_data = {
        'reference_id': fis_parsed[1],
        'amount': amount,
        'sent_to': to_proxy
    }

    return True, res_data


async def update_stores(ctx: Context, customer_id, client_id, stores):
    cm_repo = customers.CustomersMappingRepo(ctx.db)

    # clear old mappings
    deleted = await cm_repo.remove_mappings(customer_id, client_id)

    added = await cm_repo.add_stores(client_id, customer_id, stores)

    mappings = await cm_repo.get_by_customer_id(customer_id)

    return True, mappings


async def update_passphrase(ctx: Context, customer_id, old_pass, new_pass):
    repo = customers.CustomersRepo(ctx.db)

    rec = await repo.get_by_customer_id(customer_id)

    if not rec:
        return False, errors.E['customers_identifier_not_found']

    pass_match = sek.pass_match(old_pass, rec['passphrase'])
    if not pass_match:
        return False, errors.E['customers_invalid_credentials']

    updated = await repo.update_passphrase(customer_id, new_pass)
    if updated:
        return True, customers.Customer.from_record(updated)

    else:
        return False, errors.E['customers_no_security_update']


async def update_person_id(ctx: Context, customer_id, person_id):
    repo = customers.CustomersRepo(ctx.db)

    rec = await repo.get_by_customer_id(customer_id)

    if not rec:
        return False, errors.E['customers_identifier_not_found']

    updated = await repo.update_person_id(customer_id, person_id)
    if updated:
        return True, customers.Customer.from_record(updated)

    else:
        return False, errors.E['customers_invalid_person_id']


async def update_proxy(ctx: Context, customer_id, proxy):
    repo = customers.CustomersRepo(ctx.db)

    rec = await repo.get_by_customer_id(customer_id)

    if not rec:
        return False, errors.E['customers_identifier_not_found']

    updated = await repo.update_proxy(customer_id, proxy)
    if updated:
        status_updated = await change_status( ctx ,'assigned',proxy)
        if status_updated:
            return True, customers.Customer.from_record(updated)
        else:
            return False, errors.E['customers_cannot_update_proxy_status']

    else:
        return False, errors.E['customers_invalid_person_id']


async def _change_status(ctx: Context, customer_id, status, failure_message):
    repo = customers.CustomersRepo(ctx.db)

    exists = await repo.get_by_customer_id(customer_id)

    if not exists:
        return False, errors.E['customers_id_not_found']

    rec = await repo.change_status(customer_id, status)

    if rec:
        return True, customers.Customer.from_record(rec)
    else:
        return False, failure_message


async def start_reset_pass(ctx: Context, identifier):
    repo = customers.CustomersRepo(ctx.db)
    srepo = reset_sek.SecurityRepo(ctx.redis)

    _ident = customers.clean_phone_number(identifier)
    exists = await repo.get_by_identifier(_ident)

    if not exists:
        return False, errors.E['customers_identifier_not_found']

    token = reset_sek.generate_token()
    key = reset_sek.make_key(token)
    stored = await srepo.store_token(key, _ident, exists['customer_id'])

    if not stored:
        return False, errors.E['customers_unable_to_write_security_reset']

    # send via twilio
    message = sms.send_reset_pass_msg(_ident, token)
    logger.warning("passphrase reset token sent result",
                   identifier=_ident,
                   token=token,
                   message_res=message)

    return True, token


async def finish_reset_pass(ctx: Context, token, passphrase):
    repo = customers.CustomersRepo(ctx.db)
    srepo = reset_sek.SecurityRepo(ctx.redis)

    key = reset_sek.make_key(token)
    data = await srepo.get_token(key)
    if not data:
        return False, errors.E['customers_invalid_reset_token']

    updated = await repo.update_passphrase(data['entity_id'], passphrase)

    if not updated:
        return False, errors.E['customers_no_security_update']

    return True, customers.Customer.from_record(updated)


async def add_customer_address(ctx: Context, customer_id, street, city, region,
                               country, postal_code, street2=None, street3=None):
    crepo = customers.CustomersRepo(ctx.db)
    arepo = customers.AddressesRepo(ctx.db)

    exists = await crepo.get_by_customer_id(customer_id)

    if not exists:
        return False, errors.E['customers_id_not_found']

    # do we want to prevent duplicate addresses?
    # TODO: find out how important this is.
    addy = await arepo.add_address(customer_id, street, city, region, country,
                                   postal_code, street2=street2, street3=street3)

    return (True, customers.Address.from_record(addy)) if addy else (False, errors.E['customers_unable_add_address'])


#
# reads
#
async def view_customer(ctx: Context, customer_id):
    repo = customers.CustomersRepo(ctx.db)
    m_repo = customers.CustomerStoresRepo(ctx.db)

    rec = await repo.get_by_customer_id(customer_id)
    maps = await m_repo.get_by_customer_id(customer_id)
    _maps = [m['store_id'] for m in maps]

    if rec:
        return True, customers.Customer.from_record(rec, _maps)
    else:
        return False, errors.E['customers_id_not_found']


async def get_customer_proxies(ctx: Context, customer_id, status=None):
    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)

    if status:
        recs = await r_repo.search(customer_id=customer_id,
                                   proxy_status=status)
    else:
        recs = await r_repo.search(customer_id=customer_id)

    if not recs:
        return False, errors.E['customers_no_proxies']

    return (True, [card_proxies.CustomerCardProxy.from_record(r) for r in recs])


async def get_customer_proxy_details(ctx: Context, customer_id, proxy):
    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)

    rec = await r_repo.view_customer_proxy(customer_id, proxy)

    if not rec:
        return False, errors.E['customers_invalid_proxy_for_customer']

    return True, card_proxies.CustomerCardProxy.from_record(rec)


async def get_customer_proxy_status(ctx: Context, customer_id, proxy):
    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)

    rec = await r_repo.view_customer_proxy(customer_id, proxy)

    if not rec:
        return False, errors.E['customers_invalid_proxy_for_customer']

    # TODO: check FIS status as well
    fis_res, fis_data = await fis_client.get_proxy_status(rec['proxy'])

    if not fis_res:
        return False, errors.E['customers_unable_to_retrieve_proxy_status']

    fis_parsed = fis_client.parse_pipe_response(fis_data)
    res_data = {
        'proxy_status': fis_parsed[0].lower(),
        'exp_date': fis_parsed[1],
        'proxy': rec['proxy'],
        'customer_id': customer_id
    }

    return True, res_data

async def get_balance(ctx: Context, customer_id):
    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)
    rec = await r_repo.get_customer_active_proxy(customer_id)
    if not rec:
        return False, errors.E['customers_no_active_proxy']

    fis_res, fis_data = await fis_client.get_proxy_balance(rec['proxy'])
    if not fis_res:
        return False, errors.E['customers_unable_to_retrieve_balance']

    fis_parsed = fis_client.parse_pipe_response(fis_data)
    res_data = {
        'current_balance': fis_parsed[0],
        'proxy': fis_parsed[1],
        'customer_id': customer_id
    }

    return True, res_data


async def get_transactions(ctx: Context, customer_id):
    c_repo = customers.CustomersRepo(ctx.db)
    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)

    cust_proxy = await r_repo.get_customer_active_proxy(customer_id)

    if not cust_proxy:
        return False, errors.E['customers_no_active_proxy']

    fis_res, fis_data = await fis_client.get_proxy_transactions(cust_proxy['proxy'])
    if not fis_res:
        return False, errors.E['customers_unable_retrieve_txns']

    logger.warning("######>>> GET TXNS ---> ", res=fis_res, data=fis_data)
    return True, fis_data


async def get_customer_proxy_balance(ctx: Context, customer_id, proxy):
    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)
    rec = await r_repo.view_customer_proxy(customer_id, proxy)

    if not rec:
        return False, errors.E['customers_invalid_proxy_for_customer']

    fis_res, fis_data = await fis_client.get_proxy_balance(proxy)
    if not fis_res:
        return False, errors.E['customers_unable_to_retrieve_balance']

    fis_parsed = fis_client.parse_pipe_response(fis_data)
    res_data = {
        'current_balance': fis_parsed[0],
        'proxy': fis_parsed[1]
    }

    return True, res_data


async def get_customer_address_by_id(ctx: Context, customer_id, address_id):
    arepo = customers.AddressesRepo(ctx.db)

    rec = await arepo.search(customer_id=customer_id, address_id=address_id)

    if not rec:
        return False, errors.E['customers_address_not_found']

    return True, customers.Address.from_record(rec[0])


async def get_customer_addresses(ctx: Context, customer_id):
    arepo = customers.AddressesRepo(ctx.db)

    recs = await arepo.search(customer_id=customer_id)
    return (True, [customers.Address.from_record(r) for r in recs])


async def search_customers(ctx: Context, client_id=None):
    c_repo = customers.CustomersRepo(ctx.db)

    if client_id:
        recs = await c_repo.search(client_id=client_id)
    else:
        recs = await c_repo.search()

    return True, [customers.Customer.from_record(r) for r in recs]


# TODO: kill this
async def get_proxy_from_customer_id(ctx: Context, customer_id):
    repo = customers.CustomersRepo(ctx.db)

    rec = await repo.get_proxy_from_customer_id(customer_id)

    if rec:
        return True, rec
    else:
        return False, errors.E['customers_id_not_found']


#
# helpers
#
async def do_login(ctx: Context, identifier, passphrase):
    crepo = customers.CustomersRepo(ctx.db)
    srepo = sessions.SessionsRepo(ctx.redis)

    _identifier = customers.clean_phone_number(identifier)

    rec = await crepo.get_by_identifier(_identifier)
    if not rec:
        return False, None, errors.E['customers_identifier_not_found']


    pass_match = sek.pass_match(passphrase, rec['passphrase'])
    if not pass_match:
        return False, None, errors.E['customers_invalid_credentials']

    honeypot = '{}'.format(uuid.uuid1()).replace('-','')
    session_id = '{}'.format(uuid.uuid4()).replace('-','')
    ses_key = sessions.make_session_key(session_id)

    rec_data = sessions.record_to_dict(rec)
    rec_data['honeypot'] = honeypot

    data = await srepo.create(session_id, ses_key, rec['customer_id'],
                              sessions.ENTITY_TYPE_CUSTOMER, rec_data)
    ret_data = {
        'customer_id': rec['customer_id'],
        'identifier': rec['identifier'],
        'customer_status': rec['customer_status'],
        'honeypot': honeypot,
        'session_id': session_id
    }

    return True, session_id, ret_data


async def do_logout(ctx: Context, session_id):
    srepo = sessions.SessionsRepo(ctx.redis)
    ses_key = sessions.make_session_key(session_id)

    data = await srepo.get(ses_key)

    if not data:
        return False, errors.E['customers_invalid_authorization']

    deleted = await srepo.remove(ses_key)
    if not deleted:
        return False, errors.E['customers_unable_to_clear_session']

    return True, deleted


async def view_session(ctx: Context, session_id):
    srepo = sessions.SessionsRepo(ctx.redis)
    ses_key = sessions.make_session_key(session_id)

    data = await srepo.get(ses_key)

    if not data:
        return False, errors.E['customers_invalid_authorization']

    ret_data = {
        'customer_id': data['entity_id'],
        'identifier': data['data']['identifier'],
        'customer_status': data['data']['customer_status'],
        'honeypot': data['data']['honeypot'],
        'john_stewart': session_id
    }

    return True, ret_data


async def check_status(ctx: Context, proxy):
    repo = card_proxies.ClientCardProxiesRepo(ctx.db)

    cust = await repo.check_status(proxy)
    if cust:
        return True, card_proxies.CardProxy.from_record(cust)
    else:
        return False, errors.E['proxy_key_not_found']


async def change_status(ctx: Context, status, proxy):
    repo = card_proxies.ClientCardProxiesRepo(ctx.db)

    proxy = await repo.change_status('assigned',proxy)

    if proxy:
        return True
    else:
        return False, errors.E['invalid_status_code']


async def check_stores_exist(ctx: Context, store_ids):
    s_repo = stores.StoresRepo(ctx.db)
    exists = []
    not_exists = []

    for s in store_ids:
        r = await s_repo.get_by_store_id(s)
        if r:
            exists.append(r)
        else:
            not_exists.append(s)

    return exists, not_exists


async def check_employee_exists(ctx: Context, client_id, stores_data):
    cm_repo = customers.CustomersMappingRepo(ctx.db)
    exists = []
    not_exists = []

    for s in stores_data:
        r = await cm_repo.check_employee_exists(client_id, s.employee_id, s.store_id)
        if r:
            exists.append(r)
        else:
            not_exists.append(s)

    return exists, not_exists
