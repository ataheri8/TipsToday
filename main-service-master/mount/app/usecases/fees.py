from app.common import logger, errors
from app.usecases.context import Context

from app.domain import fees
from app.domain import clients

from app.common import security as sek
from app.common import json as json_util


EVENT_TYPE_SEND_ETRANSFER = 'etransfer_send'

#
# writes
#
async def create(ctx: Context, client_id, event_type, fee_value,
                 fee_type=fees.FEE_TYPE_FIXED,
                 currency_code=fees.DEFAULT_CURRENCY_CODE):
    f_repo = fees.FeesRepo(ctx.db)
    c_repo = clients.ClientsRepo(ctx.db)    

    client_exists = await c_repo.get_by_client_id(client_id)
    if not client_exists:
        return False, errors.E['fees_invalid_client_id']

    # check that this fee doesn't already exists for client
    fee_exists = await f_repo.search(client_id=client_id, event_type=event_type,
                                     fee_status=fees.STATUS_ACTIVE)
    if fee_exists:
        return False, errors.E['fees_exists_for_event_type']

    rec = await f_repo.create(client_id, event_type, fee_value,
                              fee_type=fee_type, currency_code=currency_code)
    if rec:
        return True, fees.Fee.from_record(rec)    
    else:
        return False, errors.E['fees_unable_to_create']

async def disable(ctx: Context, fee_id, client_id):
    changed = await _change_status(ctx, client_id, fee_id, fees.STATUS_INACTIVE,
                                   errors.E['fees_unable_to_disable'])
    return changed


async def enable(ctx: Context, client_id, fee_id):
    changed = await _change_status(ctx, client_id, fee_id, fees.STATUS_ACTIVE,
                                   errors.E['fees_unable_to_enable'])
    return changed


async def _change_status(ctx: Context, client_id, fee_id, status, failure_message):
    f_repo = fees.FeesRepo(ctx.db)

    exists = await f_repo.get_by_fee_id(fee_id)

    if not exists:
        return False, errors.E['fees_id_not_found']

    rec = await f_repo.change_status(fee_id, status)

    if rec:
        return True, fees.Fee.from_record(rec)
    else:
        return False, failure_message


#
# reads
#
async def view_fee(ctx: Context, fee_id):
    f_repo = fees.FeesRepo(ctx.db)

    rec = await f_repo.search(fee_id=fee_id)
    if rec:
        return True, fees.Fee.from_record(rec[0])
    else:
        return False, errors.E['fees_id_not_found']


