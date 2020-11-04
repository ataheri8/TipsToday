import uuid
from typing import List

import arrow

from pydantic import BaseModel

from app.usecases.context import Context

from app.common import logger, errors
from app.common import json as json_util

from app.domain import customers, bill_payments, card_proxies

from app.services import dcbank, bill_payments_client, fis_client



class PayeeOut(BaseModel):
    payee_id: int
    customer_id: int
    name: str
    code: str
    account_number: str
    status: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_payee(d):
        return PayeeOut(
            payee_id=d.payee_id,
            customer_id=d.customer_id,
            name=d.payee_name,
            code=d.payee_code,
            account_number=d.account_number,
            status=d.payee_status,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )




#
# writes
#
async def create_payee(ctx: Context, customer_id, payee_name, payee_code, account_number,
                       status=bill_payments.STATUS_ACTIVE):
    bp_repo = bill_payments.BillPayeesRepo(ctx.db)

    exists = await bp_repo.search(customer_id=customer_id, payee_name=payee_name,
                                  account_number=account_number)
    if exists:
        return False, errors.E['bill_payments_payee_exists']
    
    rec = await bp_repo.create(customer_id, payee_name, payee_code, account_number)

    if not rec:
        return False, errors.E['bill_payments_cannot_create_payee']
    
    return True, bill_payments.BillPayee.from_record(rec)


async def disable_payee(ctx: Context, customer_id, payee_id):
    bp_repo = bill_payments.BillPayeesRepo(ctx.db)

    exists = await bp_repo.get_payee_details(customer_id, payee_id)   
    
    if not exists:
        return False, errors.E['bill_payments_payee_not_found']

    rec = await bp_repo.change_status(payee_id, bill_payments.STATUS_INACTIVE)

    if not rec:
        return False, errors.E['bill_payemns_cannot_disable_payee']

    return True, bill_payments.BillPayee.from_record(rec)


async def update_payee_account_number(ctx: Context, customer_id, payee_id, account_number):
    bp_repo = bill_payments.BillPayeesRepo(ctx.db)

    exists = await bp_repo.get_payee_details(customer_id, payee_id)   
    
    if not exists:
        return False, errors.E['bill_payments_payee_not_found']

    rec = await bp_repo.update_account_number(payee_id, account_number)
    if not rec:
        return False, errors.E['bill_payments_cannot_update_payee']
    
    return True, bill_payments.BillPayee.from_record(rec)
    

async def create_bill_payment(ctx: Context, customer_id, payee_id, payment_amount):
    bp_repo = bill_payments.BillPayeesRepo(ctx.db)
    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)

    exists = await bp_repo.get_payee_details(customer_id, payee_id)   
    
    if not exists:
        return False, errors.E['bill_payments_payee_not_found']

    active_proxy = r_repo.get_customer_active_proxy(customer_id)
    if not active_proxy:
        return False, errors.E['customers_no_active_proxy']
    
    bal_res, bal_data = await fis_client.get_proxy_balance(active_proxy['proxy'])

    if not bal_res:
        return False, errors.E['bill_payments_unable_to_check_proxy']

    # work with absolute values for a bit
    amount = abs(payment_amount)
    bal_parsed = fis_client.parse_pipe_response(bal_data)
    balance = bal_parsed[0]

    if balance < amount:
        return False, errors.E['bill_payments_insufficent_funds']
    
    # take the money from the card
    comment = 'Bill payment - {}'.format(exists['payee_name'])
    _amount = amount * -1  # ensure we're taking money off

    adj_res, adj_data = await fis_client.proxy_adjust_value(active_proxy['proxy'], _amount, 'DEBIT',
                                                            comment)
    if not adj_res:
        return False, errors.E['bill_payments_cannot_debit_amount']

    # create the bill payment
    bill_pay_res, bill_pay_data = await bill_payments_client.create_bill_payment(exists['payee_name'],
                                                                                 exists['payee_code'],
                                                                                 amount,
                                                                                 exists['account_number'])
    if not bill_pay_res:
        # put the money back on the card
        reload_res, reload_data = await fis_client.proxy_adjust_value(active_proxy['proxy'], amount,
                                                                      'CREDIT', 'Reversing bill payment')
        return False, errors.E['bill_payments_unable_to_create_payment']

    return True, bill_payments.BillPayment(payment_amount=amount, payee_name=exists['payee_name'],
                                           account_number=exists['account_number'],
                                           submitted_at=arrow.utcnow().isoformat())

#
# reads
#
async def search_available_payees(ctx: Context, customer_id, token):
    token_len = len(token)
    if token_len < 3:
        return False, errors.E['bill_payments_search_token_too_small']

    bp_res, bp_data = await bill_payments_client.search_bill_payees(token)

    if not bp_res:
        return False, errors.E['bill_payments_no_remote_search']
    
    items = bp_data['Item']
    search_results = [bill_payments_client.PayeeSearch.from_record(i) for i in items]
    return True, search_results


async def get_customer_active_payees(ctx: Context, customer_id):
    bp_repo = bill_payments.BillPayeesRepo(ctx.db)

    recs = await bp_repo.search(customer_id=customer_id, payee_status=bill_payments.STATUS_ACTIVE)

    return True, [bill_payments.BillPayee.from_record(r) for r in recs]


async def get_payee_details(ctx: Context, customer_id, payee_id):
    bp_repo = bill_payments.BillPayeesRepo(ctx.db)

    rec = await bp_repo.get_payee_details(customer_id, payee_id)

    if rec:
        return True, bill_payments.BillPayee.from_record(rec)
    
    return False, errors.E['bill_payments_payee_no_exist_customer']

#
# helpers
#

