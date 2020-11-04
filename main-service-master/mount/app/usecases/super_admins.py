import uuid
import csv
from decimal import Decimal

from app.common import logger, errors
from app.common import security as sek
from app.common import json as json_util

from app.usecases.context import Context

from app.domain import super_admins, sessions, customers, card_proxies

from app.usecases import wallets
from app.services import fis_client
from app.services import FIS_Calls, Sanitize_Calls
#
# writes
#
async def create(ctx: Context, identifier, passphrase, first_name, last_name):
    sa_repo = super_admins.SuperAdminsRepo(ctx.db)

    exists = await sa_repo.get_by_identifier(identifier)

    if exists:
        return False, errors.E['super_admins_identifier_exists']
    
    rec = await sa_repo.create(identifier, passphrase, first_name, last_name)

    if rec:
        return True, super_admins.SuperAdmin.from_record(rec)
    
    else:
        return False, errors.E['super_admins_unable_to_create']


async def disable(ctx: Context, super_admin_id):
    changed = await _change_status(ctx,
                                   super_admin_id,
                                   super_admins.STATUS_INACTIVE,
                                   errors.E['super_admins_unable_to_disable'])
    return changed


async def enable(ctx: Context, super_admin_id):
    changed = await _change_status(ctx,
                                   super_admin_id,
                                   super_admins.STATUS_ACTIVE,
                                   errors.E['super_admins_unable_to_enable'])
    return changed


async def _change_status(ctx: Context, super_admin_id, status, failure_message):
    sa_repo = super_admins.SuperAdminsRepo(ctx.db)
    
    exists = await sa_repo.get_by_super_admin_id(super_admin_id)

    if not exists:
        return False, errors.E['super_admins_id_not_found']

    rec = await sa_repo.change_status(super_admin_id, status)

    if rec:
        return True, super_admins.SuperAdmin.from_record(rec)

    else:
        return False, failure_message


#
# reads
#
async def view_super_admin(ctx: Context, super_admin_id):
    sa_repo = super_admins.SuperAdminsRepo(ctx.db)

    rec = await sa_repo.get_by_super_admin_id(super_admin_id)

    if rec:
        return True, super_admins.SuperAdmin.from_record(rec)
    else:
        return False, errors.E['super_admins_id_not_found']


async def check_customer_card_status(ctx: Context, customer_id):
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
    sa_repo = super_admins.SuperAdminsRepo(ctx.db)
    s_repo = sessions.SessionsRepo(ctx.redis)

    rec = await sa_repo.get_by_identifier(identifier)
    if not rec:
        return False, None, errors.E['super_admins_identifier_not_found']

    if rec['super_admin_status'] != super_admins.STATUS_ACTIVE:
        return False, None, errors.E['super_admins_not_active']
    
    pass_match = sek.pass_match(passphrase, rec['passphrase'])
    if not pass_match:
        return False, None, errors.E['super_admins_invalid_credentials']
    
    honeypot = sessions.gen_session_key()
    session_id = sessions.gen_session_key()
    ses_key = sessions.make_session_key(session_id)

    rec_data = sessions.record_to_dict(rec)
    rec_data['honeypot'] = honeypot

    data = await s_repo.create(session_id, ses_key, rec['super_admin_id'],
                               sessions.ENTITY_TYPE_SUPER_ADMIN, rec_data)
    ret_data = {
        'super_admin_id': rec['super_admin_id'],
        'identifier': rec['identifier'],
        'super_admin_status': rec['super_admin_status'],
        'honeypot': honeypot,
        'session_id': session_id
    }

    return True, session_id, ret_data


async def do_logout(ctx: Context, session_id):
    s_repo = sessions.SessionsRepo(ctx.redis)
    ses_key = sessions.make_session_key(session_id)

    data = await s_repo.get(ses_key)

    if not data:
        return False, errors.E['super_admins_invalid_authorization']
    
    deleted = await s_repo.remove(ses_key)
    if not deleted:
        return False, errors.E['super_admins_unable_to_clear_session']

    return True, deleted


async def view_session(ctx: Context, session_id):
    s_repo = sessions.SessionsRepo(ctx.redis)
    ses_key = sessions.make_session_key(session_id)

    data = await s_repo.get(ses_key)
    if not data:
        return False, errors.E['super_admins_invalid_authorization']

    ret_data = {
        'super_admin_id': data['entity_id'],
        'identifier': data['data']['identifier'],
        'super_admin_status': data['data']['super_admin_status'],
        'honeypot': data['data']['honeypot'],
        'session_id': session_id
    }

    return True, ret_data


async def load_from_csvfile(ctx: Context, client_id, wallet_id,file_path):
    repo = customers.CustomersRepo(ctx.db)
    added = []
    not_added = []
    wallet_found,wallet = await wallets.find_client_wallet(ctx,client_id,wallet_id)
    total_load_amount = Decimal(0.00)
    sufficient_funds = True
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            total_load_amount = total_load_amount + Decimal(row['Amount'])
    
    if(total_load_amount <= wallet.current_amount):
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                user_exists = await repo.get_by_identifier(row['Mobile Number'])
                if(user_exists and wallet_found):
                    print(f"about to load {row['Amount']} for user with phone number {row['Mobile Number']} and with clientID {user_exists['client_id']} with wallet  {wallet.current_amount}")
                    debited, debit_data = await wallets.debit_wallet(ctx,client_id,wallet_id,row['Amount'])
                    if(debited):
                        await FIS_Calls.load_value(3930600106493, float(row['Amount']))
                        added.append(row)
                        

                else:
                    not_added.append(row)

    _added = [a['Amount'] for a in added]
    _not_added = [a['Mobile Number'] for a in not_added]


    return True, _added, _not_added
