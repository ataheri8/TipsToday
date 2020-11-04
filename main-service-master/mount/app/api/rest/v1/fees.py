import decimal
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel

from app.common import logger, errors
from app.api.rest import responses, authorizations

from app.api.rest.context import RequestContext

from app.usecases import fees


router = APIRouter()


#
# Inputs
#
class NewFeeIn(BaseModel):
    client_id: int
    event_type: str
    fee_value: str
    fee_type: str = "fixed"
    currency_code: str = "CAD"


class ChangeStatusIn(BaseModel):
    client_id: int

#
# Outputs
#
class FeeOut(BaseModel):
    fee_id: int
    client_id: int
    event_type: str
    fee_type: str
    fee_value: str
    currency_code: str
    status: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_fee(d):
        return FeeOut(
            fee_id=d.fee_id,
            client_id=d.client_id,
            event_type=d.event_type,
            fee_type=d.fee_type,
            fee_value=d.fee_value,
            currency_code=d.currency_code,
            status=d.status,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )



@router.post("/fees", response_model=FeeOut,
             dependencies=[Depends(authorizations.super_admins)])
async def create_fee(args: NewFeeIn, ctx: RequestContext = Depends()):
    made, data = await fees.create(ctx, args.client_id, args.event_type,
                                   args.fee_value,
                                   fee_type=args.fee_type,
                                   currency_code=args.currency_code)
    if made:
        resp = FeeOut.from_fee(data)
        return responses.success(resp, status_code=201)

    else:
        err = responses.format_error(data, "Unable to create")
        return responses.failure(err)


@router.get("/fees/{fee_id}", response_model=FeeOut,
            dependencies=[Depends(authorizations.super_admins)])
async def view_fee(fee_id: int, ctx: RequestContext = Depends()):
    got, data = await fees.view_fee(ctx, fee_id)

    if got:
        resp = FeeOut.from_fee(data)
        return responses.success(resp)

    else:
        err = responses.format_error(data, "unable to view")
        return responses.failure(err, status_code=404)


@router.delete("/fees/{fee_id}", response_model=FeeOut,
               dependencies=[Depends(authorizations.super_admins)])
async def disable_fee(fee_id: int, args: ChangeStatusIn,
                          ctx: RequestContext = Depends()):
    unmade, data = await fees.disable(ctx, fee_id, args.client_id)

    if unmade:
        resp = FeeOut.from_fee(data)
        return responses.success(resp)

    else:
        err = responses.format_error(data, "unable to disable")
        return responses.failure(err)

