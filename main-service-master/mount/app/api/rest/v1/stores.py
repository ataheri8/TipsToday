import decimal
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.common import logger, errors
from app.api.rest import responses, authorizations

from app.api.rest.context import RequestContext
from app.usecases import stores, wallets

router = APIRouter()


#
# inputs
#
class NewStoreIn(BaseModel):
    client_id: int
    store_name: str
    company_name: str
    card_load_identifier: str
    pad_weekday: int
    street: str
    city: str
    region: str
    postal_code: str
    country: str = "CA"
    street2: str = ""
    street3: str = ""
    lat: float = None
    lng: float = None
    admins: List[int] = []


class NewStoreBankAccountIn(BaseModel):
    transit_number: str
    institution_number: str
    account_number: str


class NewWalletIn(BaseModel):
    client_id: int
    wallet_name: str
    alert_amount: decimal.Decimal


class WalletFundIn(BaseModel):
    client_id: int
    amount: float

#
# Outputs
#
class StoreOut(BaseModel):
    store_id: int
    store_name: str
    company_name: str
    card_load_identifier: str
    status: str
    client_id: int
    created_at: str
    updated_at: str
    pad_weekday: int
    admins: List[int] = []
    wallets: List[int] = []

    @staticmethod
    def from_store(d):
        return StoreOut(
            store_id=d.store_id,
            store_name=d.store_name,
            company_name=d.company_name,
            card_load_identifier=d.card_load_identifier,
            status=d.status,
            client_id=d.client_id,
            created_at=d.created_at,
            updated_at=d.updated_at,
            pad_weekday=d.pad_weekday,
            admins=d.admins,
            wallets=d.wallets,
        )

class StoreAddressOut(BaseModel):
    address_id: int
    store_id: int
    street: str
    city: str
    region: str
    country: str
    postal_code: str
    created_at: str
    updated_at: str
    status: str
    street2: str = ""
    street3: str = ""
    lat: float = None
    lng: float = None

    @staticmethod
    def from_address(d):
        return StoreAddressOut(
            address_id=d.address_id,
            store_id=d.store_id,
            street=d.street,
            city=d.city,
            region=d.region,
            country=d.country,
            postal_code=d.postal_code,
            status=d.address_status,
            created_at=d.created_at,
            updated_at=d.updated_at,
            street2=d.street2,
            street3=d.street3,
            lat=d.lat,
            lng=d.lng,
        )


class StoreWalletActivityOut(BaseModel):
    client_id: int
    wallet_id: int
    store_id: int
    adjustment_amount: float
    previous_amount: float
    total_amount: float
    adjusted_at: str
    adjuster_id: int
    adjuster_type: str

    @staticmethod
    def from_wallet_activity(d):
        return StoreWalletActivityOut(
            client_id=d.client_id,
            wallet_id=d.wallet_id,
            store_id=d.store_id,
            adjustment_amount=d.adjustment_amount,
            previous_amount=d.previous_amount,
            total_amount=d.total_amount,
            adjusted_at=d.created_at,
            adjuster_id=d.adjuster_id,
            adjuster_type=d.adjuster_type,
        )


class StoreBankAccountOut(BaseModel):
    store_bank_account_id: int
    store_id: int
    transit_number: str
    institution_number: str
    account_number: str
    created_at: str
    updated_at: str
    status: str

    @staticmethod
    def from_bank_account(d):
        return StoreBankAccountOut(
            store_bank_account_id=d.store_bank_account_id,
            store_id=d.store_id,
            transit_number=d.transit_number,
            institution_number=d.institution_number,
            account_number=d.account_number,
            status=d.store_bank_account_status,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )


@router.post("/stores", response_model=StoreOut,
             dependencies=[Depends(authorizations.super_admins)])
async def create_store(args: NewStoreIn, ctx: RequestContext = Depends()):
    made, data = await stores.create(ctx, args.store_name, args.client_id, args.street, args.city,
                                     args.region, args.country, args.postal_code, args.pad_weekday,
                                     args.company_name, args.card_load_identifier,
                                     street2=args.street2, street3=args.street3, lat=args.lat,
                                     lng=args.lng, admins=args.admins)
    if made:
        resp = StoreOut.from_store(data)
        return responses.success(resp, status_code=201)

    else:
        err = responses.format_error(data, "Unable to create")
        return responses.failure(err)


@router.get("/stores", response_model=List[StoreOut],
            dependencies=[Depends(authorizations.super_admins)])
async def view_stores(client_id: int = None,
                      is_active: bool = None,
                      ctx: RequestContext = Depends()):
    found, data = await stores.find(ctx,
                                    client_id=client_id,
                                    active_only=is_active)

    sall = [StoreOut.from_store(d) for d in data]
    return responses.success(sall)


@router.get("/stores/{store_id}", response_model=StoreOut,
            dependencies=[Depends(authorizations.admins)])
async def view_store(store_id: int, ctx: RequestContext = Depends()):
    got, data = await stores.view_store(ctx, store_id)
    if got:
        resp = StoreOut.from_store(data)
        return responses.success(resp)

    else:
        err = responses.format_error(data, "unable to view")
        return responses.failure(err, status_code=404)


@router.delete("/stores/{store_id}", dependencies=[Depends(authorizations.super_admins)])
async def disable_store(store_id: int, ctx: RequestContext = Depends()):
    unmade, data = await stores.disable(ctx, store_id)

    if unmade:
        resp = StoreOut.from_store(data)
        return responses.success(resp)

    else:
        err = responses.format_error(data, "unable to disable")
        return responses.failure(err)


@router.post("/stores/{store_id}/bank-accounts", response_model=StoreBankAccountOut,
             dependencies=[Depends(authorizations.admins)])
async def add_store_bank_account(store_id: int, args: NewStoreBankAccountIn,
                                 ctx: RequestContext = Depends()):
    res, data = await stores.add_store_bank_account(ctx,
                                                    store_id,
                                                    args.transit_number,
                                                    args.institution_number,
                                                    args.account_number)

    if res:
        resp = StoreBankAccountOut.from_bank_account(data)
        return responses.success(resp)

    err = responses.format_error(data, "bank account add failure")
    return responses.failure(err)


@router.get("/stores/{store_id}/bank-accounts", response_model=List[StoreBankAccountOut],
            dependencies=[Depends(authorizations.admins)])
async def get_store_bank_accounts(store_id: int, ctx: RequestContext = Depends()):
    _, data = await stores.get_store_bank_accounts(ctx, store_id)

    resp = [StoreBankAccountOut.from_bank_account(d) for d in data]
    return responses.success(resp)


@router.get("/stores/{store_id}/bank-accounts/{bank_account_id}", response_model=StoreBankAccountOut,
            dependencies=[Depends(authorizations.admins)])
async def get_store_bank_account_details(store_id: int, bank_account_id: int,
                                         ctx: RequestContext = Depends()):
    res, data = await stores.get_bank_account(ctx, store_id, bank_account_id)

    if res:
        resp = StoreBankAccountOut.from_bank_account(data)
        return responses.success(resp)

    err = responses.format_error(data, "unable to get bank account details")
    return responses.failure(err, status_code=404)


@router.post("/stores/{store_id}/bank-accounts/{bank_account_id}", response_model=StoreBankAccountOut,
             dependencies=[Depends(authorizations.admins)])
async def update_store_bank_account_details(store_id: int, bank_account_id: int,
                                            args: NewStoreBankAccountIn,
                                            ctx: RequestContext = Depends()):
    res, data = await stores.update_store_bank_account(ctx,
                                                       store_id,
                                                       bank_account_id,
                                                       args.transit_number,
                                                       args.institution_number,
                                                       args.account_number)
    if res:
        resp = StoreBankAccountOut.from_bank_account(data)
        return responses.success(resp)

    err = responses.format_error(data, "unable to update bank account details")
    return responses.failure(err)


@router.get("/stores/{store_id}/wallets", response_model=wallets.StoreWalletOut,
            dependencies=[Depends(authorizations.admins)])
async def view_store_wallets(store_id: int,
                             admin_id: int = None,
                             is_active: bool = None,
                             ctx: RequestContext = Depends()):

    found, data = await wallets.find(ctx,
                                     store_id=store_id,
                                     admin_id=admin_id,
                                     active_only=is_active)
    wall = [wallets.StoreWalletOut.from_wallet(d) for d in data]
    return responses.success(wall)


@router.post("/stores/{store_id}/wallets", response_model=wallets.StoreWalletOut,
             dependencies=[Depends(authorizations.super_admins)])
async def add_store_wallet(store_id: int, args: NewWalletIn,
                          ctx: RequestContext = Depends()):
    made, data = await wallets.add_wallet(ctx,
                                          args.client_id,
                                          store_id,
                                          args.wallet_name,
                                          args.alert_amount)

    if made:
        resp = wallets.StoreWalletOut.from_wallet(data)
        return responses.success(resp, status_code=201)
    else:
        err = responses.format_error(data, "not available")
        return responses.failure(err)


@router.get("/stores/{store_id}/wallets/{wallet_id}",
            response_model=wallets.StoreWalletOut,
            dependencies=[Depends(authorizations.admins)])
async def view_store_wallet(store_id: int, wallet_id: int,
                            ctx: RequestContext = Depends()):

    found, data = await wallets.find_store_wallet(ctx, store_id, wallet_id)

    if found:
        resp = wallets.StoreWalletOut.from_wallet(data)
        return responses.success(resp)
    else:
        status_code = 404 if (data == errors.E['wallets_id_not_found']) else 400
        err = responses.format_error(data, "invalid wallet")
        return responses.failure(err, status_code=status_code)


@router.get("/stores/{store_id}/wallets/{wallet_id}/history",
            dependencies=[Depends(authorizations.admins)])
async def view_store_wallet_adjustments(store_id: int,
                                        wallet_id: int,
                                        start_date: str = "",
                                        end_date: str = "",
                                        ctx: RequestContext = Depends()):
    found, data = await wallets.view_activity(ctx,
                                              wallet_id,
                                              store_id,
                                              start_date,
                                              end_date)

    resp = [StoreWalletActivityOut.from_wallet_activity(d) for d in data]
    return responses.success(resp)


@router.post("/stores/{store_id}/wallets/{wallet_id}/adjust",
             response_model=wallets.StoreWalletOut,
             dependencies=[Depends(authorizations.admins)])
async def adjust_wallet(store_id: int, wallet_id: int, args: WalletFundIn,
                        ctx: RequestContext = Depends()):
    entity_id = ctx.session.get('entity_id')
    entity_type = ctx.session.get('entity_type')

    updated, data = await wallets.fund_wallet(ctx,
                                              args.client_id,
                                              store_id,
                                              wallet_id,
                                              args.amount,
                                              entity_id,
                                              entity_type)

    if updated:
        resp = wallets.StoreWalletOut.from_wallet(data)
        return responses.success(resp)
    else:
        status_code = 404 if (data == errors.E['wallets_id_not_found']) else 400
        err = responses.format_error(data, "invalid wallet")
        return responses.failure(err, status_code=status_code)


@router.get("/stores/{store_id}/addresses", response_model=List[StoreAddressOut],
            dependencies=[Depends(authorizations.admins)])
async def view_store_addresses(store_id: int, is_active: bool = True,
                               ctx: RequestContext = Depends()):
    res, data = await stores.get_store_addresses(ctx, store_id, active_only=is_active)

    if res:
        resp = [StoreAddressOut.from_address(d) for d in data]
        return responses.success(resp)

    err = responses.format_error(data, "cannot load addresses")
    return responses.failure(err)


@router.get("/stores/{store_id}/addresses/{address_id}", response_model=StoreAddressOut,
            dependencies=[Depends(authorizations.admins)])
async def view_store_addresses(store_id: int, address_id: int,
                               ctx: RequestContext = Depends()):
    res, data = await stores.get_address(ctx, store_id, address_id)

    if res:
        resp = StoreAddressOut.from_address(data)
        return responses.success(resp)

    err = responses.format_error(data, "cannot load address")
    return responses.failure(err)
