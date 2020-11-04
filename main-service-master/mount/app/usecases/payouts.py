from pydantic import BaseModel

from app.common import logger, errors
from app.usecases.context import Context

from app.domain import admins
from app.domain import wallets
from app.domain import clients
from app.domain import customers
from app.domain import card_proxies
from app.domain import card_transactions

from app.common import security as sek
from app.common import json as json_util

from app.services import fis_client


CURRENCY_CAD = 'CAD'
CURRENCY_USD = 'USD'

ENTITY_TYPE_SUPER_ADMIN = 'super-admin'
ENTITY_TYPE_COMPANY_ADMIN = 'company-admin'
ENTITY_TYPE_STORE_ADMIN = 'store-admin'
ENTITY_TYPE_CUSTOEMR = 'customer'

EVENT_TYPE_LOAD = 'card-load'

TXN_STATUS_PENDING = 'pending'
TXN_STATUS_COMPLETE = 'complete'

#
# inputs
#
# Putting this here, because this is being used by super admins and admins
class PayoutIn(BaseModel):
    customer_id: int
    store_id: int
    amount: float
    description: str = ""


#
# outputs
#
class CardProxy(BaseModel):
    id: int
    client_id: int
    proxy: str
    status: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_record(rec):
        return CardProxy(
            id=rec['rec_id'],
            client_id=rec['client_id'],
            proxy=rec['proxy'],
            status=rec['proxy_status'],
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at')
        )

class PayoutOut(BaseModel):
    payout_id: str
    customer_id: int
    proxy: str
    actor_id: int
    actor_type: str
    payout_type: str
    currency_code: str
    amount: float
    status: str
    created_at: str
    description: str = ''

    @staticmethod
    def from_payout_txn(d):
        return PayoutOut(
            payout_id=d.txn_id,
            customer_id=d.customer_id,
            proxy=d.proxy,
            actor_id=d.entity_id,
            actor_type=d.entity_type,
            payout_type=d.event_type,
            currency_code=d.currency_code,
            amount=d.txn_amount,
            status=d.txn_status,
            created_at=d.created_at,
            description=d.description,
        )



#
# writes
#
async def create_payout(ctx: Context, customer_id, amount, store_id, entity_id,
                        entity_type, currency_code=CURRENCY_CAD, description=''):
    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)
    t_repo = card_transactions.TxnsRepo(ctx.db)
    w_repo = wallets.WalletsRepo(ctx.db)
    a_repo = wallets.WalletsAuditRepo(ctx.db)

    cust_proxy = await r_repo.get_customer_active_proxy(customer_id)
    
    if not cust_proxy:
        return False, errors.E['customers_no_active_proxy']
    
    txn_id = card_transactions.generate_txn_id()

    # check the wallet balance
    active_wallets = await w_repo.get_by_store_id(store_id)
    if not active_wallets:
        return False, errors.E['stores_no_active_wallet']

    has_balance = wallets.check_balances_against_amount(active_wallets, amount)
    if not has_balance:
        return False, errors.E['stores_insufficient_wallet_balance']

    # start the payout
    init_payout = await t_repo.create_payout(txn_id,
                                             customer_id,
                                             cust_proxy['proxy'],
                                             entity_id,
                                             entity_type,
                                             EVENT_TYPE_LOAD,
                                             amount,
                                             TXN_STATUS_PENDING,
                                             currency_code,
                                             description)

    if not init_payout:
        return False, errors.E['admins_unable_to_create_payout']
    
    # adjust the wallet balance
    if amount < 0:  # we are taking money off the card
        wallet_marked = await w_repo.increment(active_wallets[0]['wallet_id'],
                                               amount)
    
    else:  # we are putting money on the card
        wallet_marked = await w_repo.decrement(active_wallets[0]['wallet_id'],
                                               amount)

    if not wallet_marked:
        return False, errors.E['wallets_unable_to_decrement']
    
    # audit the wallet adjustment
    audit = await a_repo.add_entry(active_wallets[0]['wallet_id'],
                                   active_wallets[0]['client_id'],
                                   store_id,
                                   active_wallets[0]['current_amount'],
                                   amount,
                                   has_balance,
                                   entity_id,
                                   entity_type)

    # make the call to FIS
    call_res, call_data = await fis_client.proxy_load_value(cust_proxy['proxy'],
                                                            amount)

    if not call_res:
        return False, errors.E['admins_unable_to_adjust_amount_processor']

    # complete the payout
    comp_payout = await t_repo.complete_payout(txn_id,
                                               entity_id,
                                               entity_type,
                                               TXN_STATUS_COMPLETE)

    if not comp_payout:
        return False, errors.E['admins_unable_to_complete_payout']
    

    # return a Txn data class object
    return True, card_transactions.PayoutTxn.from_record(comp_payout)


#
# reads
#
async def view_payout_details(ctx: Context, payout_id):
    t_repo = card_transactions.TxnsRepo(ctx.db)
    _recs = await t_repo.get_by_txn_id(payout_id)

    recs = [card_transactions.PayoutTxn.from_record(r) for r in _recs]

    return True, recs
