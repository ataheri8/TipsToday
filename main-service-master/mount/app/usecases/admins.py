import csv

from pydantic import BaseModel

from app.common import logger, errors
from app.usecases.context import Context

from app.domain import admins, sessions
from app.domain import wallets
from app.domain import clients
from app.domain import customers
from app.domain import card_proxies

from app.common import security as sek
from app.common import json as json_util

from app.services import fis_client


#
# Shared Outputs
#
class AdminOut(BaseModel):
    admin_id: int
    identifier: str
    first_name: str
    last_name: str
    status: str
    level: str
    client_id: int
    created_at: str
    updated_at: str
    title: str = ""

    @staticmethod
    def from_admin(d):
        return AdminOut(
            admin_id=d.admin_id,
            identifier=d.identifier,
            first_name=d.first_name,
            last_name=d.last_name,
            status=d.status,
            level=d.level,
            client_id=d.client_id,
            created_at=d.created_at,
            updated_at=d.updated_at,
            title=d.title,
        )



#
# writes
#
async def create(ctx: Context, identifier, passphrase, first_name, last_name,
                 client_id, level, title=""):
    sa_repo = admins.AdminsRepo(ctx.db)
    c_repo = clients.ClientsRepo(ctx.db)

    exists = await sa_repo.get_by_identifier(identifier)
    
    if exists:
        return False, errors.E['admins_identifier_exists']

    # ensure that the client and wallet exist
    client_exists = await c_repo.get_by_client_id(client_id)
    if not client_exists:
        return False, errors.E['admins_invalid_client_id']
    
    rec = await sa_repo.create(identifier, passphrase, first_name, last_name,
                               client_id, level, title=title)

    if rec:
        return True, admins.Admin.from_record(rec)  
    else:
        return False, errors.E['admins_unable_to_create']

async def load_from_csvfile(ctx: Context, client_id, file_path):
    c_repo = customers.CustomersRepo(ctx.db)
    sa_repo = admins.AdminsRepo(ctx.db)
    added = []
    not_added = []

    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            user_exists = await c_repo.get_by_identifier(row['Mobile Number'])
            
            if(user_exists):
                print(f"about to load {row['Amount']} for user with phone number {row['Mobile Number']} and with clientID {user_exists['client_id']} ")
            
    _added = [a['identifier'] for a in added]
    return True, _added, not_added


async def disable(ctx: Context, admin_id):
    changed = await _change_status(ctx, admin_id, admins.STATUS_INACTIVE,
                                   errors.E['admins_unable_to_disable'])
    return changed


async def enable(ctx: Context, admin_id):
    changed = await _change_status(ctx, admin_id, admins.STATUS_ACTIVE,
                                   errors.E['admins_unable_to_enable'])
    return changed


async def _change_status(ctx: Context, admin_id, status, failure_message):
    sa_repo = admins.AdminsRepo(ctx.db)

    exists = await sa_repo.get_by_admin_id(admin_id)    

    if not exists:
        return False, errors.E['admins_id_not_found']

    rec = await sa_repo.change_status(admin_id, status)

    if rec:
        return True, admins.Admin.from_record(rec)
    else:
        return False, failure_message


#
# reads
#
async def view_admin(ctx: Context, admin_id):
    sa_repo = admins.AdminsRepo(ctx.db)
    rec = await sa_repo.get_by_admin_id(admin_id)

    if rec:
        return True, admins.Admin.from_record(rec)
    else:
        return False, errors.E['admins_id_not_found']


async def get_all_admins(ctx: Context, client_id):
    sa_repo = admins.AdminsRepo(ctx.db)
    recs = await sa_repo.get_all_admins(client_id)
    found = [admins.Admin.from_record(r) for r in recs]

    return True, found


async def search_admins(ctx: Context, client_id=None):
    sa_repo = admins.AdminsRepo(ctx.db)

    if client_id:
        recs = await sa_repo.search(client_id=client_id)
    else:
        recs = await sa_repo.search()

    return True, [admins.Admin.from_record(r) for r in recs]


async def check_status(ctx: Context, proxy):
    sa_repo = admins.AdminsRepo(ctx.db)

    cust = await sa_repo.check_status(proxy)

    if cust:
        return True, admins.Admin.from_record(cust)
    else:
        return False, errors.E('proxy_key_not_found')


async def check_customer_card_balance(ctx: Context, admin_id, customer_id):
    # ensure that this admin can view this customer's information
    can_do = await _admin_can_view_customer(ctx, admin_id, customer_id)
    if not can_do: 
        return False, errors.E['admins_invalid_customer_access']

    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)

    cust_proxy = await r_repo.get_customer_active_proxy(customer_id)
    if not cust_proxy:
        return False, errors.E['customers_no_active_proxy']

    fis_res, fis_data = await fis_client.get_proxy_balance(cust_proxy['proxy'])
    if not fis_res:
        return False, errors.E['customers_unable_to_retrieve_balance']

    fis_parsed = fis_client.parse_pipe_response(fis_data)
    res_data = {
        'current_balance': fis_parsed[0],
        'proxy': fis_parsed[1],
        'customer_id': customer_id
    }

    return True, res_data


async def check_customer_card_status(ctx: Context, admin_id, customer_id):
    # ensure that this admin can view this customer's information
    can_do = await _admin_can_view_customer(ctx, admin_id, customer_id)
    if not can_do: 
        return False, errors.E['admins_invalid_customer_access']

    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)

    cust_proxy = await r_repo.get_customer_active_proxy(customer_id)
    if not cust_proxy:
        return False, errors.E['customers_no_active_proxy']

    fis_res, fis_data = await fis_client.get_proxy_status(cust_proxy['proxy'])

    if not fis_res:
        return False, errors.E['customers_unable_to_retrieve_proxy_status']

    fis_parsed = fis_client.parse_pipe_response(fis_data)
    res_data = {
        'proxy_status': fis_parsed[0].lower(),
        'exp_date': fis_parsed[1],
        'proxy': cust_proxy['proxy'],
        'customer_id': customer_id
    }

    return True, res_data


#
# helpers
#
async def do_login(ctx: Context, identifier, passphrase):
    sa_repo = admins.AdminsRepo(ctx.db)
    s_repo = sessions.SessionsRepo(ctx.redis)

    rec = await sa_repo.get_by_identifier(identifier)
    if not rec:
        return False, None, errors.E['admins_identifier_not_found']

    if rec['admin_status'] != admins.STATUS_ACTIVE:
        return False, None, errors.E['admins_not_active']

    pass_match = sek.pass_match(passphrase, rec['passphrase'])
    if not pass_match:
        return False, None, errors.E['admins_invalid_credentials']

    honeypot = sessions.gen_session_key()
    session_id = sessions.gen_session_key()
    ses_key = sessions.make_session_key(session_id)

    rec_data = sessions.record_to_dict(rec)
    rec_data['honeypot'] = honeypot

    _entity_type = sessions.ENTITY_TYPE_STORE_ADMIN
    if rec['level'] == admins.LEVEL_COMPANY:
        _entity_type = sessions.ENTITY_TYPE_COMPANY_ADMIN

    data = await s_repo.create(session_id,
                               ses_key,
                               rec['admin_id'],
                               _entity_type,
                               rec_data)
    ret_data = {
        'admin_id': rec['admin_id'],
        'identifier': rec['identifier'],
        'admin_status': rec['admin_status'],
        'level': rec['level'],
        'honeypot': honeypot,
        'session_id': session_id
    }

    return True, session_id, ret_data


async def do_logout(ctx: Context, session_id):
    s_repo = sessions.SessionsRepo(ctx.redis)
    ses_key = sessions.make_session_key(session_id)

    data = await s_repo.get(ses_key)

    if not data:
        return False, errors.E['admins_invalid_authorization']

    deleted = await s_repo.remove(ses_key)
    if not deleted:
        return False, errors.E['admins_unable_to_clear_session']

    return True, deleted


async def view_session(ctx: Context, session_id):
    s_repo = sessions.SessionsRepo(ctx.redis)
    ses_key = sessions.make_session_key(session_id)

    data = await s_repo.get(ses_key)
    if not data:
        return False, errors.E['admins_invalid_authorization']

    ret_data = {
        'admin_id': data['entity_id'],
        'identifier': data['data']['identifier'],
        'admin_status': data['data']['admin_status'],
        'level': data['data']['level'],
        'honeypot': data['data']['honeypot'],
        'session_id': session_id
    }

    return True, ret_data


async def _admin_can_view_customer(ctx: Context, admin_id, customer_id):
    sa_repo = admins.AdminsRepo(ctx.db)
    c_repo = customers.CustomersRepo(ctx.db)
    
    # initially just checking that the customer and admin are of the same client
    # unclear if we need to limit this to a specific store...
    _admin = await sa_repo.get_by_admin_id(admin_id)
    _customer = await c_repo.get_by_customer_id(customer_id)

    return _admin['client_id'] == _customer['client_id']
