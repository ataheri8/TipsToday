import decimal
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel
import shutil
from pathlib import Path
from app.common import logger, errors

from app.api.rest import responses,authorizations
from app.usecases import super_admins, admins, clients, customers, payouts, wallets, stores

from app.domain import card_proxies
from app.services import FIS_Calls, DC_Bank_Calls



from app.api.rest.context import RequestContext

router = APIRouter()


#
# inputs
#
class SuperAdminLogin(BaseModel):
    identifier: str
    passphrase: str


class NewSuperAdminIn(SuperAdminLogin):
    identifier: str
    passphrase: str
    first_name: str
    last_name: str


class SuperAdminChangeStatusIn(BaseModel):
    status: str
    customer_id: int


class SuperAdminCheckStatusIn(BaseModel):
    customer_id: int


class SuperAdminLoadIn(BaseModel):
    customer_id: int
    amount: float


class SuperAdminCardToCardIn(BaseModel):
    customer_id: int
    receiver_proxy: str
    amount: float


#
# outputs
#
class SuperAdminOut(BaseModel):
    super_admin_id: int
    identifier: str
    first_name: str
    last_name: str
    status: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_super_admin(d):
        return SuperAdminOut(
            super_admin_id=d.super_admin_id,
            identifier=d.identifier,
            first_name=d.first_name,
            last_name=d.last_name,
            status=d.status,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )


class SuperAdminSessionOut(BaseModel):
    super_admin_id: int
    identifier: str
    status: str
    session_id: str
    clark_kent: str


class ClientOut(BaseModel):
    client_id: str
    status: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_client(d):
        return ClientOut(
            program_name=d.program_name,
            program_type=d.program_type,
            network=d.network,
            sponsoring_bank=d.sponsoring_bank,
            program_bin=d.program_bin,
            program_bin_range=d.program_bin_range,
            processor=d.processor,
            printer=d.printer,
            printer_client_id=d.printer_client_id,
            printer_package_id=d.printer_package_id,
            card_type=d.card_type,
            card_order_type=d.card_order_type,
            card_order_frequency=d.card_order_frequency,
            client_id=d.client_id,
            status=d.status,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )


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


@router.post("/super-admins", response_model=SuperAdminOut)
async def create_super_admin(args: NewSuperAdminIn,
                             ctx: RequestContext = Depends()):
    made, data = await super_admins.create(ctx, args.identifier, args.passphrase,
                                           args.first_name, args.last_name)    
    if made:
        resp = SuperAdminOut.from_super_admin(data)
        return responses.success(resp, status_code=201)
    else:
        err = responses.format_error(data, "not available")
        return responses.failure(err)


@router.get("/super-admins/{super_admin_id}", dependencies=[Depends(authorizations.super_admins)])
async def view_super_admin(super_admin_id: int, ctx: RequestContext = Depends()):
    got, data = await super_admins.view_super_admin(ctx, super_admin_id)

    if got:
        resp = SuperAdminOut.from_super_admin(data)
        return responses.success(resp)

    else:
        err = responses.format_error(data, "not found")
        return responses.failure(err, status_code=404)


@router.delete("/super-admins/{super_admin_id}",
               dependencies=[Depends(authorizations.super_admins)])
async def disable_super_admin(super_admin_id: int,
                              ctx: RequestContext = Depends()):
    unmade, data = await super_admins.disable(ctx, super_admin_id)

    if unmade:
        resp = admins.SuperAdminOut.from_super_admin(data)
        return responses.success(resp)
    else:
        err = responses.format_error(data, "unable to disable")
        return responses.failure(err)


@router.post("/super-admin-sessions", response_model=SuperAdminSessionOut)
@router.post("/super-admin-login", response_model=SuperAdminSessionOut)
async def login_super_admin(args: SuperAdminLogin,
                            ctx: RequestContext = Depends()):
    authed, session_id, sdata = await super_admins.do_login(ctx,
                                                            args.identifier,
                                                            args.passphrase)

    if authed:
        resp = SuperAdminSessionOut(super_admin_id=sdata['super_admin_id'],
                                    identifier=sdata['identifier'],
                                    status=sdata['super_admin_status'],
                                    session_id=sdata['honeypot'],
                                    clark_kent=session_id)

        return responses.success(resp, status_code=201)
    else:
        err = responses.format_error(sdata, "invalid authorization")
        return responses.failure(err, status_code=401)
        

@router.delete("/super-admin-sessions",
               dependencies=[Depends(authorizations.super_admins)])
@router.delete("/super-admin-logout",
               dependencies=[Depends(authorizations.super_admins)])
async def logout_super_admin(ctx: RequestContext = Depends()):
    cleared, data = await super_admins.do_logout(ctx, session_id)
    if not cleared:
        err = responses.format_error(data, "")
        return responses.failure(err)

    resp = {"session_id": ""}
    return responses.success(resp)


@router.get("/super-admin-sessions/{session_id}",
            response_model=SuperAdminSessionOut,
            dependencies=[Depends(authorizations.super_admins)])
async def view_super_admin_session(session_id: str, ctx: RequestContext = Depends()):
    found, sdata = await super_admins.view_session(ctx, session_id)

    if not found:
        err = responses.format_error(sdata, "")
        return responses.failure(err)
    
    resp = SuperAdminSessionOut(super_admin_id=sdata['super_admin_id'],
                                identifier=sdata['identifier'],
                                status=sdata['super_admin_status'],
                                session_id=sdata['honeypot'],
                                clark_kent=sdata['session_id'])

    return responses.success(resp)


# previously /admins/{admin_id}/clients/{client_id}/managers
@router.get("/super-admins/{super_admin_id}/clients/{client_id}/admins",
            response_model=List[admins.AdminOut],
            dependencies=[Depends(authorizations.super_admins)])
async def view_client_admins(super_admin_id: int,
                               client_id: int,
                               ctx: RequestContext = Depends()):
    
    found, data = await admins.get_all_admins(ctx, client_id)
  
    resp = [admins.AdminOut.from_admin(d) for d in data]

    return responses.success(resp)


@router.get("/super-admins/{super_admin_id}/clients",
            response_model=List[ClientOut],
            dependencies=[Depends(authorizations.super_admins)])
async def list_clients(super_admin_id: int, ctx: RequestContext = Depends()):
    found, data = await clients.get_all(ctx)

    resp = [ClientOut.from_client(d) for d in data]
    return responses.success(resp)


@router.get("/super-admins/{super_admin_id}/customers", response_model=List[customers.CustomerOut],
            dependencies=[Depends(authorizations.super_admins)])
async def super_admin_customers_search(super_admin_id: int,
                                       client_id: int = None,
                                       ctx: RequestContext = Depends()):
    _, data = await customers.search_customers(ctx, client_id=client_id)

    resp = [customers.CustomerOut.from_customer(d) for d in data]
    return responses.success(resp)

@router.get("/super-admins/{super_admin_id}/wallets", response_model=List[wallets.StoreWalletOut],
            dependencies=[Depends(authorizations.super_admins)])
async def super_admin_wallets_search(super_admin_id: int,
                                     client_id: int = None,
                                     ctx: RequestContext = Depends()):
    _, data = await wallets.find(ctx, client_id=client_id)

    resp = [wallets.StoreWalletOut.from_wallet(d) for d in data]
    return responses.success(resp)


@router.get("/super-admins/{super_admin_id}/admins", response_model=List[admins.AdminOut],
            dependencies=[Depends(authorizations.super_admins)])
async def super_admin_admin_search(super_admin_id: int,
                                   client_id: int = None,
                                   ctx: RequestContext = Depends()):
    _, data = await admins.search_admins(ctx, client_id=client_id)

    resp = [admins.AdminOut.from_admin(d) for d in data]
    return responses.success(resp)


@router.get("/super-admins/{super_admin_id}/stores/{store_id}/customers",
            response_model=List[customers.CustomerOut],
            dependencies=[Depends(authorizations.super_admins)])
async def super_admins_view_store_customers(super_admin_id: int, store_id: int,
                                            ctx: RequestContext = Depends()):
    _, data = await stores.get_store_customers(ctx, store_id)

    resp = [customers.CustomerOut.from_customer(c) for c in data]
    return responses.success(resp)


async def getCustomersToStore(store_id:int, ctx: RequestContext = Depends()):
   
    found, data = await admins.get_customers_from_store(ctx, store_id)
    
    if found:
        resp = [CustomerOut.from_customer(d) for d in data]
        return responses.success(resp, status_code=201)
    else:
        err = responses.format_error("", "Store ID does not exist")
        return responses.failure(err)

@router.post("/super-admins/{super_admin_id}/clients/{client_id}/wallets/{wallet_id}/bulk-transfer",
             dependencies=[Depends(authorizations.super_admins)])
async def load_cards_from_file(super_admin_id: int,
                               wallet_id: int,
                               client_id: int,
                               transfer_file: UploadFile = File(...),
                               ctx: RequestContext = Depends()):
    file_name = f"{wallet_id}_bulk_transfer.csv"
    path_name = "/tmp/{}".format(file_name)
    destination = Path(path_name)
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(transfer_file.file, buffer)

    finally:
        _ = await transfer_file.close()

    # process the file.
    ok, added, not_added = await admins.load_from_csvfile(ctx, client_id, wallet_id, path_name)

    resp = {
        'status': ok,
        'added': len(added),
        'added_details': added,
        'not_added': len(not_added),
        'not_added_details': not_added
    }
    return responses.success(resp)


@router.post("/super-admins/{super_admin_id}/change-status")
async def changeStatus(super_admin_id: int,
                       args: SuperAdminChangeStatusIn,
                       ctx: RequestContext = Depends()):

    card_proxies_repo = card_proxies.ClientCardProxiesRepo(ctx.db)

    found, proxy = await customers.get_proxy_from_customer_id(ctx, args.customer_id)

    if found:
        get_proxy = dict(proxy)['proxy']
        data = await card_proxies_repo.change_status(args.status, get_proxy)

        if data:
            sent, status = await FIS_Calls.change_status(args.status, get_proxy)
            if sent:
                resp = CardProxy.from_record(data)
                return responses.success(resp, status_code=201)
            else:
                return responses.failure(p, status_code=422)
        else:
            err = responses.format_error(data, "Incorrect proxy number or status code")
            return responses.failure(err)
    else:
        err = responses.format_error("", "Unable to grab proxy")
        return responses.failure(err)


@router.post("/super-admins/{super_admin_id}/payouts", response_model=payouts.PayoutOut,
             dependencies=[Depends(authorizations.super_admins)])
async def super_admin_create_payout(super_admin_id: int, args: payouts.PayoutIn,
                                    ctx: RequestContext = Depends()):
    res, data = await payouts.create_payout(ctx,
                                            args.customer_id,
                                            args.amount,
                                            args.store_id,
                                            super_admin_id,
                                            payouts.ENTITY_TYPE_SUPER_ADMIN,
                                            description=args.description)
    if not res:
        err = responses.format_error(data, "unable to create payout")
        return responses.failure(err)
    
    resp = payouts.PayoutOut.from_payout_txn(data)
    return responses.success(resp)


@router.get("/super-admins/{super_admin_id}/payouts/{payout_id}",
            response_model=List[payouts.PayoutOut],
            dependencies=[Depends(authorizations.super_admins)])
async def view_payout_details(super_admin_id: int, payout_id: str,
                              ctx: RequestContext = Depends()):
    _, data = await payouts.view_payout_details(ctx, payout_id)

    resp = [payouts.PayoutOut.from_payout_txn(d) for d in data]
    return responses.success(resp)


@router.get("/super-admins/{super_admin_id}/customers/{customer_id}/balance",
            dependencies=[Depends(authorizations.super_admins)])
async def super_admin_view_customer_balance(super_admin_id: int,
                                            customer_id: int,
                                            ctx: RequestContext = Depends()):
    res, data = await customers.get_balance(ctx, customer_id)

    if not res:
        err = responses.format_error(data, "unable to retrieve balance")
        return responses.failure(err)
    
    # TODO: turn this into a proper output class
    return responses.success(data)


@router.get("/super-admins/{super_admin_id}/customers/{customer_id}/card-status",
            dependencies=[Depends(authorizations.super_admins)])
async def super_admin_view_customer_card_status(super_admin_id: int,
                                                customer_id: int,
                                                ctx: RequestContext = Depends()):
    res, data = await super_admins.check_customer_card_status(ctx, customer_id)

    if not res:
        err = responses.format_error(data, "unable to retrieve status")
        return responses.failure(err)
    
    # TODO: turn this into a proper output class
    return responses.success(data)



@router.post("/super-admins/{super_admin_id}/card-to-card")
async def cardToCard(super_admin_id: int,
                     args: SuperAdminCardToCardIn,
                     ctx: RequestContext = Depends()):

    found, proxy = await customers.get_proxy_from_customer_id(ctx, args.customer_id)

    if found:
        get_proxy = dict(proxy)['proxy']
        sent, data = await FIS_Calls.card_to_card_transfer(get_proxy, args.receiver_proxy, args.amount)

        if sent:
            return responses.success(data, status_code=201)
        else:
            return responses.failure(data, status_code=422)
    else:
        err = responses.format_error("", "Unable to grab proxy")
        return responses.failure(err)


@router.get("/super-admins/{super_admin_id}/customers/{customer_id}/transactions",
            dependencies=[Depends(authorizations.super_admins)])
async def view_customer_transactions(super_admin_id: int, customer_id: int,
                                     ctx: RequestContext = Depends()):
    
    res, data = await customers.get_transactions(ctx, customer_id)

    if not res:
        err = responses.format_error(data, "unable to fetch transactions")
        return responses.failure(err)

    # TODO: make a response class for this
    return responses.success(data)
    

# @router.get("/admins/{admin_id}/transactions")
# async def getTransactions(AdminCheckStatusIn, ctx: RequestContext = Depends()):

#     found, proxy = await customers.get_proxy_from_customer_id(ctx, args.customer_id)

#     if found:
#         get_proxy = dict(proxy)['proxy']
#         updated, data = await FIS_Calls.get_transactions(get_proxy, args.StartDate, args.Days)
    
#         if updated is True:
#             return responses.success(data, status_code=201)
#         else:
#             return responses.failure(data, status_code=422)
#     else:
#         err = responses.format_error("", "Unable to grab proxy")
#         return responses.failure(err)


