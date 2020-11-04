import uuid
from typing import List

import arrow
from pydantic import BaseModel

from app.usecases.context import Context

from app.common import logger, errors, chrono
from app.common import json as json_util

from app.domain import customers, sessions, etransfers, card_proxies, fees

from app.services import dcbank, etransfers_client, fis_client


DEFAULT_COUNTRY = 'canada'
DEFAULT_REGION = 'ontario'


class RecipientOut(BaseModel):
    recipient_id: int
    customer_id: int
    name: str
    email: str
    security_question: str
    security_answer: str
    status: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_recipient(d):
        return RecipientOut(
            recipient_id=d.recipient_id,
            customer_id=d.customer_id,
            name=d.recipient_name,
            email=d.email_address,
            security_question=d.security_question,
            security_answer=d.security_answer,
            status=d.recipient_status,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )


class EtransferOut(BaseModel):
    amount: float
    fee_amount: float
    recipient_name: str
    submitted_at: str
    transaction_id: str

    @staticmethod
    def from_etransfer(d):
        return EtransferOut(
            amount=d.amount,
            fee_amount=d.fee_amount,
            recipient_name=d.recipient_name,
            submitted_at=d.submitted_at,
            transaction_id=d.transaction_id,
        )


#
# writes
#
async def create_recipient(ctx: Context, customer_id, rec_name, rec_email, sec_question, sec_answer,
                           dc_contact_id=None, country=DEFAULT_COUNTRY, region=DEFAULT_REGION):
    er_repo = etransfers.EtransferRecipientsRepo(ctx.db)

    question_check, question_error = handle_security_question(sec_question)
    if not question_check:
        return False, question_error

    answer_check, answer_data = handle_security_answer(sec_answer)
    if not answer_check:
        return False, answer_data

    # does this recipient already exist
    exists = await er_repo.search(only_one=True, customer_id=customer_id, recipient_name=rec_name)

    if exists:
        return False, errors.E['etransfers_recipient_exists']
    
    rec = await er_repo.create(customer_id, rec_name, rec_email, sec_question, answer_data,
                               dc_contact_id=dc_contact_id)
    if not rec:
        return False, errors.E['etransfers_cannot_create_recipient']
   
    first_name, last_name = get_names(rec_name)

    # update dc bank...
    dc_res, dc_data = await etransfers_client.create_contact(first_name, last_name, rec_email)

    if not dc_res:
        return False, errors.E['etransfers_cannot_create_remote_contact']

    contact_id = '{}'.format(dc_data['Item'])
    # update local record with dc contact id
    updated = await er_repo.update_contact_id(rec['recipient_id'], contact_id)

    if not updated:
        return False, errors.E['etransfers_cannot_create_recipient']
    
    return True, etransfers.EtransferRecipient.from_record(updated)
      

async def update_recipient(ctx: Context, customer_id, recipient_id, rec_name, rec_email,
                           sec_question, sec_answer, dc_contact_id=None, country=DEFAULT_COUNTRY,
                           region=DEFAULT_REGION):
    er_repo = etransfers.EtransferRecipientsRepo(ctx.db)

    # does this recipient already exist
    exists = await er_repo.search(only_one=True, customer_id=customer_id, recipient_name=rec_name)

    if not exists:
        return False, errors.E['etransfers_invalid_recipient_id']

    question_check, question_error = handle_security_question(sec_question)
    if not question_check:
        return False, question_error

    answer_check, answer_data = handle_security_answer(sec_answer)
    if not answer_check:
        return False, answer_data

    dc_update_needed = requires_dc_update(rec_name, rec_email,
                                          exists['recipient_name'], exists['email_address'])
    
    # update local records
    rec = await er_repo.update_contact(customer_id, recipient_id, rec_name, rec_email, sec_question,
                                       answer_data)

    if not rec:
        return False, errors.E['etransfers_cannot_update_recipient']

    # if dc bank update is needed, make that call
    if dc_update_needed:
        first_name, last_name = get_names(rec_name)
        dc_res, dc_data = await etransfers_client.update_contact(first_name, last_name, rec_email,
                                                                 rec['dc_contact_id'])
        if not dc_res:
            return False, errors.E['etransfers_cannot_create_remote_contact']

    
    return True, etransfers.EtransferRecipient.from_record(rec)


async def deactivate_recipient(ctx: Context, customer_id, recipient_id):
    er_repo = etransfers.EtransferRecipientsRepo(ctx.db)

    # does this recipient already exist
    exists = await er_repo.search(only_one=True, customer_id=customer_id, recipient_id=recipient_id)

    if not exists:
        return False, errors.E['etransfers_invalid_recipient_id']

    rec = await er_repo.change_status(recipient_id, etransfers.STATUS_INACTIVE)
    
    if rec:
        return True, etransfers.EtransferRecipient.from_record(rec)
    else:
        return False, errors.E['etransfers_unable_to_deactivate']


async def send_etransfer(ctx: Context, customer_id, recipient_id, amount):
    er_repo = etransfers.EtransferRecipientsRepo(ctx.db)
    e_repo = etransfers.EtransfersRepo(ctx.db)
    r_repo = card_proxies.CustomerCardProxiesRepo(ctx.db)
    f_repo = fees.FeesRepo(ctx.db)

    recipient = await er_repo.get_recipient_details(customer_id, recipient_id)

    if not recipient:
        return False, errors.E['etransfers_recipient_not_found']

    active_proxy = r_repo.get_customer_active_proxy(customer_id)
    if not active_proxy:
        return False, errors.E['customers_no_active_proxy']
    
    bal_res, bal_data = await fis_client.get_proxy_balance(active_proxy['proxy'])

    if not bal_res:
        return False, errors.E['etransfers_unable_to_check_proxy']

    # work with absolute values for a bit
    amount = abs(payment_amount)
    bal_parsed = fis_client.parse_pipe_response(bal_data)
    balance = bal_parsed[0]

    # get fees
    fee_data = await f_repo.search(only_one=True, event_type=fees.EVENT_TYPE_SEND_ETRANSFER,
                                   fee_status=fees.STATUS_ACTIVE)
    fee_amount = 0.00  # setting a default
    fee_type = 'fixed'
    if fee_data:
        fee_amount = float(fee_data['fee_value'])
        fee_type = fee_data['fee_type']

    required_balance = calc_total(amount, fee_type, fee_value)

    if balance < required_balance:
        return False, errors.E['etransfers_insufficent_funds']

    # take the money from the card
    comment = 'Etransfer - {}'.format(recipient['recipient_name'])
    _amount = amount * -1  # ensure we're taking money off
    adj_res, adj_data = await fis_client.proxy_adjust_value(active_proxy['proxy'], _amount, 'DEBIT',
                                                            comment)
    
    if fee_amount > 0:
        _fee_amount = fee_amount * -1
        fee_res, fee_data = await fis_client.proxy_adjust_value(active_proxy['proxy'], _fee_amount,
                                                                'DEBIT', 'Etransfer fee')

    if not adj_res:
        return False, errors.E['etransfers_cannot_debit_amount']

    # create the etransfer
    etransfer_res, etransfer_data = await etransfers_client.send_etransfer(amount,
                                                                           recipient['security_question'],
                                                                           recipient['security_answer'],
                                                                           recipient['dc_contact_id'])
    if not etransfer_res:
        # put the money back on the card
        reload_res, reload_data = await fis_client.proxy_adjust_value(active_proxy['proxy'], amount,
                                                                      'CREDIT', 'Reversing failed etransfer')
        if fee_amount > 0:
            fee_reload_res, fee_reload_data = await fis_client.proxy_adjust_value(active_proxy['proxy'],
                                                                                  fee_amount,
                                                                                  'CREDIT',
                                                                                  'Reversing failed etransfer fee')
        return False, errors.E['etransfers_unable_to_create_etransfer']

    # create the local record
    local_rec = await e_repo.create(customer_id, etransfer_data['Item'], amount, fee_amount,
                                    recipient['recipient_name'])

    return True, etransfers.Etransfer.from_record(local_rec)


#
# reads
#
async def get_recipient_details(ctx: Context, customer_id, recipient_id):
    er_repo = etransfers.EtransferRecipientsRepo(ctx.db)

    rec = await er_repo.get_recipient_details(customer_id, recipient_id)

    if rec:
        return True, etransfers.EtransferRecipient.from_record(rec)
    
    return False, errors.E['etransfers_recipient_not_found']


async def get_recipients(ctx: Context, customer_id, is_active=True):
    er_repo = etransfers.EtransferRecipientsRepo(ctx.db)

    if is_active:
        recs = await er_repo.search(customer_id=customer_id, recipient_status=etransfers.STATUS_ACTIVE)
    else:
        recs = await er_repo.search(customer_id=customer_id)
    
    return True, [etransfers.EtransferRecipient.from_record(r) for r in recs]


async def get_etransfers(ctx: Context, customer_id, start_date="", end_date=""):
    e_repo = etransfers.EtransfersRepo(ctx.db)
    
    if not start_date:
        _start = chrono.get_last_month_short()
    else:
        _start = chrono.format_dates_for_db(start_date)
    
    if not end_date:
        _end = arrow.utcnow().naive
    else:
        _end = chrono.format_dates_for_db(end_date)    
    
    recs = await e_repo.get_by_customer_id(customer_id, _start, _end)

    return True, [etransfers.Etransfer.from_record(r) for r in recs]


#
# helpers
#
def handle_security_answer(answer):
    len_check = len(answer)
    if len_check < 3 or len_check > 25:
        return False, errors.E['etransfers_security_answer_wrong_size']
    
    _answer = answer.replace(' ', '')
    return True, _answer


def handle_security_question(question):
    len_check = len(question)
    if len_check > 40:
        return False, errors.E['etransfers_security_question_too_long']
    
    return True, question


def get_names(rec_name):
    _names = rec_name.split(' ')
    first_name = _names[0]
    if len(_names) > 2:
        last_name = ' '.join(_names[1:])
    else:
        last_name = _names[1]
    
    return first_name, last_name


def requires_dc_update(new_name, new_email, old_name, old_email):
    if new_name.strip().lower() != old_name.strip().lower():
        return True
    
    if new_email.strip().lower() != old_email.strip().lower():
        return True

    return False


def calc_total(amount, fee_type, fee_value):
    if fee_type == 'fixed':
        return amount + fee_value
    
    if fee_type == 'percentage':
        total = amount * (1 + fee_value)
        return total


