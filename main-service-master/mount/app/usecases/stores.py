from app.common import logger, errors
from app.usecases.context import Context

from app.domain import admins, wallets, clients, stores, customers

from app.common import security as sek
from app.common import json as json_util


#
# writes
#
async def create(ctx: Context, store_name, client_id, street, city, region, country, postal_code,
                 pad_weekday, company_name, card_load_id, street2="", street3="", lat=None,
                 lng=None, admins=[]):
    s_repo = stores.StoresRepo(ctx.db)
    sa_repo = stores.AddressesRepo(ctx.db)

    s_exists = await s_repo.get_by_store_name_and_client_id(store_name, client_id)

    if s_exists:
        return False, errors.E['stores_exists_for_client']

    c_repo = clients.ClientsRepo(ctx.db)
    c_exists = await c_repo.get_by_client_id(client_id)

    # ensure that the client and wallet exist
    if not c_exists:
        return False, errors.E['stores_invalid_client_id']
    
    s_rec = await s_repo.create(store_name, client_id, pad_weekday, company_name, card_load_id, admins)

    if s_rec:
        a_rec = await sa_repo.add_address(s_rec['store_id'], street, city, region, country, postal_code,
                                          street2=street2, street3=street3, lat=lat, lng=lng)
        # we have made the store and address records
        # get the olson timezone and update the store record.
        return True, stores.Store.from_record(s_rec)
    else:
        return False, errors.E['stores_unable_to_create']


async def disable(ctx: Context, store_id):
    changed = await _change_status(ctx, store_id, stores.STATUS_INACTIVE,
                                   errors.E['stores_unable_to_disable'])
    return changed


async def enable(ctx: Context, store_id):
    changed = await _change_status(ctx, store_id, stores.STATUS_ACTIVE,
                                   errors.E['stores_unable_to_enable'])
    return changed


async def _change_status(ctx: Context, store_id, status, failure_message):
    repo = stores.StoresRepo(ctx.db)

    exists = await repo.get_by_store_id(store_id)

    if not exists:
        return False, errors.E['stores_id_not_found']

    rec = await repo.change_status(store_id, status)

    if rec:
        return True, stores.Store.from_record(rec)

    else:
        return False, failure_message


async def add_store_bank_account(ctx: Context, store_id, transit_num, institution_num, account_num):
    ba_repo = stores.StoreBankAccountsRepo(ctx.db)

    exists = await ba_repo.search(only_one=True,
                                  store_id=store_id,
                                  transit_number=transit_num,
                                  institution_number=institution_num,
                                  account_number=account_num)
    
    if exists:
        return False, errors.E['stores_bank_account_exists']
    
    rec = await ba_repo.add_bank_account(store_id, transit_num, institution_num, account_num)

    if rec:
        return True, stores.StoreBankAccount.from_record(rec)
    else:
        return False, errors.E['stores_bank_account_add_failure']


async def update_store_bank_account(ctx: Context, store_id, bank_account_id, transit_num,
                                    institution_num, account_num):
    ba_repo = stores.StoreBankAccountsRepo(ctx.db)

    exists = await ba_repo.get_by_bank_account_id(store_id, bank_account_id)

    if not exists:
        return False, errors.E['stores_bank_account_not_found']
    
    rec = await ba_repo.update_bank_account(store_id, bank_account_id, transit_num, institution_num,
                                            account_num)
    
    if rec:
        return True, stores.StoreBankAccount.from_record(rec)
    else:
        return False, errors.E['stores_bank_account_cannot_update']


#
# reads
#
async def view_store(ctx: Context, store_id):
    repo = stores.StoresRepo(ctx.db)
    wrepo = wallets.WalletsRepo(ctx.db)

    rec = await repo.get_by_store_id(store_id)
    walls = await wrepo.search(store_id=store_id,
                               wallet_status=wallets.WALLET_ACTIVE_STATUS)

    if rec:
        wallet_ids = [w.get('wallet_id') for w in walls]
        return True, stores.Store.from_record(rec, wallet_ids)

    else:
        return False, errors.E['stores_id_not_found']


async def find(ctx: Context, client_id=None, active_only=None):
    srepo = stores.StoresRepo(ctx.db)
    wrepo = wallets.WalletsRepo(ctx.db)

    kwargs = {}

    if client_id is not None:
        kwargs['client_id'] = client_id
    
    if active_only is not None:
        kwargs['store_status'] = active_only
    
    sall = await srepo.search(**kwargs)
    _all = []

    for s in sall:
        swall = await wrepo.search(store_id=s.get('store_id'),
                                   wallet_status=wallets.WALLET_ACTIVE_STATUS)
        wallet_ids = [w.get('wallet_id') for w in swall]
        _all.append(stores.Store.from_record(s, wallet_ids))

    return (True, _all) if sall else (False, _all)


async def get_store_addresses(ctx: Context, store_id, active_only=False):
    sa_repo = stores.AddressesRepo(ctx.db)

    if active_only:
        recs = await sa_repo.search(store_id=store_id, address_status=stores.STATUS_ACTIVE)
    else:
        recs = await sa_repo.search(store_id=store_id)

    _recs = [stores.StoreAddress.from_record(r) for r in recs]

    return True, _recs


async def get_address(ctx: Context, store_id, address_id):
    sa_repo = stores.AddressesRepo(ctx.db)

    rec = await sa_repo.search(only_one=True, store_id=store_id, address_id=address_id)

    if rec:
        return True, stores.StoreAddress.from_record(rec)
    else:
        return False, errors.E['stores_address_not_found']


async def get_store_bank_accounts(ctx: Context, store_id):
    ba_repo = stores.StoreBankAccountsRepo(ctx.db)

    recs = await ba_repo.get_by_store_id(store_id)

    return True, [stores.StoreBankAccount.from_record(r) for r in recs]


async def get_bank_account(ctx: Context, store_id, bank_account_id):
    ba_repo = stores.StoreBankAccountsRepo(ctx.db)

    rec = await ba_repo.get_by_bank_account_id(store_id, bank_account_id)

    if rec:
        return True, stores.StoreBankAccount.from_record(rec)
    else:
        return False, errors.E['stores_bank_account_not_found']


async def get_store_customers(ctx: Context, store_id):
    cs_repo = customers.CustomerStoresRepo(ctx.db)
    c_repo = customers.CustomersRepo(ctx.db)

    store_recs = await cs_repo.get_by_store_id(store_id)
    
    if not store_recs:
        # it's not an error really, just no customers yet
        return True, []
    
    customer_ids = [s['customer_id'] for s in store_recs]

    _custs = await c_repo.bulk_get_ints('customer_id', customer_ids)

    return True, [customers.Customer.from_record(r) for r in _custs]

