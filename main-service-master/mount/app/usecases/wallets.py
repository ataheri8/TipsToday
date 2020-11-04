import decimal

from pydantic import BaseModel

from app.common import logger, errors
from app.usecases.context import Context

from app.domain import clients, wallets, stores, super_admins, admins
from app.common import security as sek
from app.common import json as json_util
from app.common import chrono


class StoreWalletOut(BaseModel):
    client_id: int
    store_id: int
    wallet_id: int
    status: str
    current_amount: float
    created_at: str
    updated_at: str

    @staticmethod
    def from_wallet(d):
        return StoreWalletOut(
            wallet_id=d.wallet_id,
            wallet_name=d.name,
            alert_amount=d.alert_amount,
            current_amount=d.current_amount,
            client_id=d.client_id,
            store_id=d.store_id,
            status=d.status,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )


# Writes
async def add_wallet(ctx: Context, client_id, store_id, wallet_name,
                     alert_amount):
    c_repo = clients.ClientsRepo(ctx.db)
    w_repo = wallets.WalletsRepo(ctx.db)
    s_repo = stores.StoresRepo(ctx.db)

    c_exists = await c_repo.get_by_client_id(client_id)
    if not c_exists:
        return False, errors.E['clients_id_not_found']

    s_exists = await s_repo.get_by_store_id(store_id)
    if not s_exists:
        return False, errors.E['stores_id_not_found']

    # ensure that the admiin belongs to the client
    if s_exists['client_id'] != client_id:
        return False, errors.E['stores_mismatched_client_id']

    w = await w_repo.add_wallet(client_id, store_id, wallet_name, alert_amount)
    if w:
        return True, wallets.Wallet.from_record(w)
    else:
        return False, errors.E['wallets_unable_to_create']


async def deactivate(ctx: Context, client_id, wallet_id):
    wrepo = wallets.WalletsRepo(ctx.db)

    w = await wrepo.mark_wallet_inactive(wallet_id, client_id)
    if w:
        return True, wallets.Wallet.from_record(w)
    else:
        return False, errors.E['wallets_unable_to_deactivate']



async def debit_wallet(ctx: Context, client_id, wallet_id, amount):
    wrepo = wallets.WalletsRepo(ctx.db)

    w = await wrepo.get_client_wallet(client_id, wallet_id)
    if not w:
        return False, errors.E['wallets_client_wallet_mismatch']
    
    _current_amt = decimal.Decimal(w['current_amount'])
    _add_amt = decimal.Decimal(amount)
    new_amt = _current_amt - _add_amt

    updated = await wrepo.update_amount(client_id, wallet_id, new_amt)
    if not updated:
        return False, errors.E['wallets_cannot_update_amount']

    return True, wallets.Wallet.from_record(updated)


async def fund_wallet(ctx: Context, client_id, store_id, wallet_id, adj_amount,
                      entity_id, entity_type):
    w_repo = wallets.WalletsRepo(ctx.db)
    wa_repo = wallets.WalletsAuditRepo(ctx.db)
    s_repo = stores.StoresRepo(ctx.db)
    cl_repo = clients.ClientsRepo(ctx.db)
    sa_repo = super_admins.SuperAdminsRepo(ctx.db)
    a_repo = admins.AdminsRepo(ctx.db)

    _wallet = await w_repo.get_client_store_wallet(client_id, store_id, wallet_id)
    if not _wallet:
        return False, errors.E['wallets_client_wallet_mismatch']
    
    _prev_amt = decimal.Decimal(_wallet['current_amount'])
    _adj_amt = decimal.Decimal(adj_amount)
    new_amt = _prev_amt + _adj_amt

    _store = await s_repo.get_by_store_id(store_id)
    _client = await cl_repo.get_by_client_id(client_id)

    if entity_id == 'admin':
        _entity = await sa_repo.get_by_super_admin_id(entity_id)
    else:
        _entity = await a_repo.get_by_admin_id(entity_id)

    if not _entity:
        # just in case!
        _entity_name = 'Unknown'
    else:
        _entity_name = f"{_entity['first_name']} {_entity['last_name']}"

    audited = await wa_repo.add_entry(wallet_id, _wallet['wallet_name'], client_id,
                                      _client['client_name'], store_id, _store['store_name'],
                                      entity_id, entity_type, _entity_name,
                                      _prev_amt, _adj_amt, new_amt)
    
    if not audited:
        return False, errors.E['wallets_cannot_audit_adjustment']
    
    updated = await w_repo.update_amount(client_id, wallet_id, new_amt)
    if not updated:
        return False, errors.E['wallets_cannot_update_amount']

    return True, wallets.Wallet.from_record(updated)


# Reads
async def find_by_client_id(ctx: Context, client_id, active_only=True):
    wrepo = wallets.WalletsRepo(ctx.db)
    
    wallet_status = None
    if active_only:
        wallet_status = wallets.WALLET_ACTIVE_STATUS

    _wallets = await wrepo.search(client_id=client_id, wallet_status=wallet_status)
 
    _all = map(wallets.Wallet.from_record, _wallets) if _wallets else []
    
    return (True, _all) if _wallets else (False, _all)


async def find_store_wallet(ctx: Context, store_id, wallet_id):
    wrepo = wallets.WalletsRepo(ctx.db)
    wall = await wrepo.search(store_id=store_id, wallet_id=wallet_id)

    if wall:
        return True, wallets.Wallet.from_record(wall[0])
    else:
        return False, errors.E['wallets_id_not_found']


async def find_client_wallet(ctx: Context, client_id, wallet_id):
    wrepo = wallets.WalletsRepo(ctx.db)
    wall = await wrepo.search(client_id=client_id, wallet_id=wallet_id)

    if wall:
        return True, wallets.Wallet.from_record(wall[0])
    else:
        return False, errors.E['wallets_id_not_found']


async def find_client_total_wallets(ctx: Context, client_id):
    wrepo = wallets.WalletsRepo(ctx.db)
    wall = await wrepo.get_wallet_by_client_id(client_id)

    if wall:
        return True, wallets.Wallet.from_record(wall)
    else:
        return False, errors.E['client_id_not_found']


async def add_wallet_funds(ctx: Context, wallet_id, amount):
    wrepo = wallets.WalletsRepo(ctx.db)
    wall = await wrepo.add_wallet_funds(wallet_id, amount)

    if wall:
        return True, wallets.Wallet.from_record(wall)
    else:
        return False, errors.E['wallets_id_not_found']


async def find_by_id(ctx: Context, wallet_id: int):
    wrepo = wallets.WalletsRepo(ctx.db)
    wall = await wrepo.search(wallet_id=wallet_id)

    if wall:
        return True, wallets.Wallet.from_record(wall[0])
    else:
        return False, errors.E['wallets_id_not_found']


async def find(ctx: Context, client_id=None, admin_id=None, store_id=None,
               active_only=None):
    wrepo = wallets.WalletsRepo(ctx.db)
    
    kwargs = {}

    if client_id is not None:
        kwargs['client_id'] = client_id
    
    if admin_id is not None:
        kwargs['admin_id'] = admin_id
    
    if store_id is not None:
        kwargs['store_id'] = store_id

    if active_only is not None:
        kwargs['wallet_status'] = active_only
    
    wall = await wrepo.search(**kwargs)
    _all = list(map(wallets.Wallet.from_record, wall)) if wall else []
    return (True, _all) if wall else (False, _all)


async def view_activity(ctx: Context, wallet_id, store_id, start_date=None,
                        end_date=None):
    arepo = wallets.WalletsAuditRepo(ctx.db)

    if start_date:
        _start = chrono.format_dates_for_db(start_date)
    else:
        _start = chrono.get_last_week_for_db()

    if end_date:
        _end = chrono.format_dates_for_db(end_date)
    else:
        _end = chrono.get_current_time_db()

    recs = await arepo.view_activity(wallet_id, store_id, _start, _end)

    activity = list(map(wallets.WalletActivity.from_record, recs)) if recs else []
    return (True, activity) if recs else (False, recs)



#
# 
#
