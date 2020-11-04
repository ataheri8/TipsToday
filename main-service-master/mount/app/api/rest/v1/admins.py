import decimal
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel
import shutil
from pathlib import Path

from app.common import logger, errors

from app.api.rest import responses, authorizations
from app.api.rest.context import RequestContext

from app.usecases import admins, customers, payouts

from app.domain import card_proxies
from app.services import FIS_Calls, Sanitize_Calls


router = APIRouter()


#
# Inputs
#
class AdminLogin(BaseModel):
    identifier: str
    passphrase: str


class NewAdminIn(AdminLogin):
    first_name: str
    last_name: str
    level: str
    title: str = ""
    client_id: int


class AdminCheckStatusIn(BaseModel):
    customer_id: int


class AdminChangeStatusIn(BaseModel):
    customer_id: int
    status: str


#
# Outputs
#
class AdminSessionOut(BaseModel):
    admin_id: int
    identifier: str
    level: str
    status: str
    session_id: str
    barry_allen: str


@router.post("/admins", response_model=admins.AdminOut)
async def create_admin(args: NewAdminIn, ctx: RequestContext = Depends()):
    made, data = await admins.create(ctx,
                                     args.identifier,
                                     args.passphrase,
                                     args.first_name,
                                     args.last_name,
                                     args.client_id,
                                     args.level,
                                     title=args.title)

    if made:
        resp = admins.AdminOut.from_admin(data)
        return responses.success(resp, status_code=201)
    
    else:
        err = responses.format_error(data, "Unable to create")
        return responses.failure(err)


@router.get("/admins/{admin_id}")
async def view_admin(admin_id: int, ctx: RequestContext = Depends()):
    res, data = await admins.view_admin(ctx, admin_id)

    if res:
        resp = admins.AdminOut.from_admin(data)
        return responses.success(resp)
    else:
        err = responses.format_error(data, "unable to view")
        return responses.failure(err, status_code=404)


@router.delete("/admins/{admin_id}")
async def disable_admin(admin_id: int, ctx: RequestContext = Depends()):
    unmade, data = await admins.disable(ctx, admin_id)

    if unmade:
        resp = admins.AdminOut.from_admin(data)
        return responses.success(resp)
    else:
        err = responses.format_error(data, "unable to disable")
        return responses.failure(err)


@router.post("/admin-sessions", response_model=AdminSessionOut)
@router.post("/admin-login", response_model=AdminSessionOut)
async def login_admin(args: AdminLogin, ctx: RequestContext = Depends()):
    authed, session_id, sdata = await admins.do_login(ctx,
                                                      args.identifier,
                                                      args.passphrase)
    if authed:
        sdata['session_id'] = session_id
        ctx.session = sdata
        resp = AdminSessionOut(admin_id=sdata['admin_id'],
                               identifier=sdata['identifier'],
                               status=sdata['admin_status'],
                               level=sdata['level'],
                               session_id=sdata['honeypot'],
                               barry_allen=session_id)

        return responses.success(resp, status_code=201)

    else:
        err = responses.format_error(sdata, "invalid authorization")
        return responses.failure(err, status_code=401)


@router.delete("/admin-sessions", dependencies=[Depends(authorizations.admins)])
@router.delete("/admin-logout", dependencies=[Depends(authorizations.admins)])
async def logout_admin(ctx: RequestContext = Depends()):
    session_id = ctx.session['session_id']
    cleared, data = await admins.do_logout(ctx, session_id)

    if not cleared:
        err = responses.format_error(data, "")
        return responses.failure(err)

    resp = {"session_id": ""}
    ctx.session = {}
    return responses.success(resp)


@router.get("/admin-sessions", response_model=AdminSessionOut,
            dependencies=[Depends(authorizations.admins)])
async def view_admin_session(ctx: RequestContext = Depends()):
    session_id = ctx.session['session_id']
    found, data = await admins.view_session(ctx, session_id)  

    if not found:
        err = responses.format_error(data, "")
        return responses.failure(err)

    resp = AdminSessionOut(admin_id=data['admin_id'],
                           identifier=data['identifier'],
                           status=data['admin_status'],
                           level=data['level'],
                           session_id=data['honeypot'],
                           barry_allen=data['session_id'])

    return responses.success(resp)


@router.post("/admins/{admin_id}/bulk-transfer",
             dependencies=[Depends(authorizations.admins)])
async def onboard_clients_from_file(admin_id: int, transfer_file: UploadFile = File(...),
                                    ctx: RequestContext = Depends()):
    file_name = f"{admin_id}_bulk_transfer.csv"
    path_name = "/tmp/{}".format(file_name)
    destination = Path(path_name)
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(transfer_file.file, buffer)

    finally:
        _ = await transfer_file.close()

    # process the file.
    ok, added, not_added = await admins.load_from_csvfile(ctx, admin_id, path_name)

    resp = {
        'status': ok,
        'added': len(added),
        'added_details': added,
        'not_added': len(not_added),
        'not_added_details': not_added
    }
    return responses.success(resp)


@router.post("/admins/{admin_id}/change-status")
async def change_status(admin_id: int, args: AdminChangeStatusIn,
                       ctx: RequestContext = Depends()):

    card_proxies_repo = card_proxies.ClientCardProxiesRepo(ctx.db)

    found, proxy = await customers.get_proxy_from_customer_id(ctx, args.customer_id)
    
    if found:
        get_proxy = dict(proxy)['proxy']
        data = await card_proxies_repo.change_status(args.status, get_proxy)

        if data:
            sent, status = await FIS_Calls.change_status(args.status, get_proxy)
            if sent:
                resp = payouts.CardProxy.from_record(data)
                return responses.success(resp, status_code=201)
            else:
                return responses.failure(p, status_code=422)
        else:
            err = responses.format_error(data, "Incorrect proxy number or status code")
            return responses.failure(err)
    else:
        err = responses.format_error("", "Unable to grab proxy")
        return responses.failure(err)


@router.post("/admins/{admin_id}/payouts", response_model=payouts.PayoutOut,
             dependencies=[Depends(authorizations.admins)])
async def create_payout(admin_id: int, args: payouts.PayoutIn,
                        ctx: RequestContext = Depends()):
    res, data = await payouts.create_payout(ctx,
                                            args.customer_id,
                                            args.amount,
                                            args.store_id,
                                            admin_id,
                                            payouts.ENTITY_TYPE_COMPANY_ADMIN,
                                            description=args.description)
    if not res:
        err = responses.format_error(data, "unable to create payout")
        return responses.failure(err)

    
    resp = payouts.PayoutOut.from_payout_txn(data)
    return responses.success(resp)


@router.get("/admins/{admin_id}/payouts/{payout_id}",
            response_model=List[payouts.PayoutOut],
            dependencies=[Depends(authorizations.admins)])
async def view_payout_details(admin_id: int, payout_id: str,
                              ctx: RequestContext = Depends()):
    _, data = await payouts.view_payout_details(ctx, payout_id)

    resp = [payouts.PayoutOut.from_payout_txn(d) for d in data]
    return responses.success(resp)


@router.get("/admins/{admin_id}/customers/{customer_id}/balance",
            dependencies=[Depends(authorizations.admins)])
async def admin_view_customer_balance(admin_id: int, customer_id: int,
                                      ctx: RequestContext = Depends()):
    res, data = await admins.check_customer_card_balance(ctx, admin_id, customer_id)

    if not res:
        err = responses.format_error(data, "unable to retrieve balance")
        return responses.failure(err)
    
    # TODO: turn this into a proper output class
    return responses.success(data)


@router.get("/admins/{admin_id}/customers/{customer_id}/card-status",
            dependencies=[Depends(authorizations.admins)])
async def admin_view_customer_card_status(admin_id: int, customer_id: int,
                                          ctx: RequestContext = Depends()):
    res, data = await admins.check_customer_card_status(ctx, admin_id, customer_id)

    if not res:
        err = responses.format_error(data, "unable to retrieve status")
        return responses.failure(err)
    
    # TODO: turn this into a proper output class
    return responses.success(data)


# @router.get("/managers/{manager_id}/status")
# async def checkStatus(args: ManagerCheckStatusIn, ctx: RequestContext = Depends()):

#     card_proxies_repo = card_proxies.ClientCardProxiesRepo(ctx.db)

#     found, proxy = await customers.get_proxy_from_customer_id(ctx, args.customer_id)

#     if found:
#         get_proxy = dict(proxy)['proxy']
#         data = await card_proxies_repo.check_status(get_proxy)
#         receieved, status = await FIS_Calls.check_status(get_proxy)

#         if receieved:
#             resp = CardProxy.from_record(data)
#             return responses.success(resp, status_code=201)
#         else:
#             return responses.failure(resp, status_code=422)
#     else:
#         err = responses.format_error(data, "Unable to grab proxy")
#         return responses.failure(err)