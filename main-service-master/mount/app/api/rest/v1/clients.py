import shutil
import decimal
import uuid
from typing import List
from pathlib import Path


from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel


from app.common import logger, errors
from app.api.rest import responses, authorizations
from app.usecases import clients, wallets, customers


from app.api.rest.context import RequestContext

router = APIRouter()


#
# Inputs
#
class NewClientIn(BaseModel):
    program_id: int
    client_name: str
    company_name: str
    terms_and_conditions: str
    csr_instructions: str
    email_alert_address: str


class ClientFlagsIn(BaseModel):
    corp_load: int = 0
    rbc_bill_payment: int = 0
    load_hub: int = 0
    pad: int = 0
    eft: int = 0
    ach: int = 0
    card_to_card: int = 0
    e_transfer: int = 0
    bill_payment: int = 0
    bank_to_card: int = 0
    card_to_bank: int = 0
    eft_app: int = 0
    ach_app: int = 0


#
# Outputs
#
class ClientOut(BaseModel):
    client_id: str
    program_id: str
    client_name: str
    company_name: str
    status: str
    terms_and_conditions: str
    csr_instructions: str
    email_alert_address: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_client(d):
        return ClientOut(
            client_id=d.client_id,
            program_id=d.program_id,
            client_name=d.client_name,
            company_name=d.company_name,
            status=d.status,
            terms_and_conditions=d.terms_conditions,
            csr_instructions=d.csr_instructions,
            email_alert_address=d.email_alert_address,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )


class ClientFlagsOut(ClientFlagsIn):
    client_id: int
    updated_at: str
    created_at: str

    @staticmethod
    def from_flag(d):
        return ClientFlagsOut(
            client_id=d.client_id,
            corp_load=d.corp_load,
            rbc_bill_payment=d.rbc_bill_payment,
            load_hub=d.load_hub,
            pad=d.pad,
            eft=d.eft,
            ach=d.ach,
            card_to_card=d.card_to_card,
            e_transfer=d.e_transfer,
            bill_payment=d.bill_payment,
            bank_to_card=d.bank_to_card,
            card_to_bank=d.card_to_bank,
            eft_app=d.eft_app,
            ach_app=d.ach_app,
            updated_at=d.updated_at,
            created_at=d.created_at,
        )


@router.post("/clients", response_model=ClientOut,
             dependencies=[Depends(authorizations.super_admins)])
async def create_client(args: NewClientIn, ctx: RequestContext = Depends()):
    made, data = await clients.create(ctx, args.client_name, args.company_name, args.program_id,
                                      args.terms_and_conditions, args.csr_instructions, args.email_alert_address)

    if made:
        resp = ClientOut.from_client(data)
        return responses.success(resp, status_code=201)
    else:
        err = responses.format_error(data, "not available")
        return responses.failure(err)


@router.get("/clients", response_model=List[ClientOut],
            dependencies=[Depends(authorizations.super_admins)])
async def list_clients(ctx: RequestContext = Depends()):
    found, data = await clients.get_all(ctx)

    resp = [ClientOut.from_client(d) for d in data]
    return responses.success(resp)


@router.get("/clients/{client_id}", response_model=ClientOut,
            dependencies=[Depends(authorizations.super_admins)])
async def get_client(client_id: int, ctx: RequestContext = Depends()):
    found, data = await clients.find_by_id(ctx, client_id)
    if found:
        resp = ClientOut.from_client(data)
        return responses.success(resp)
    else:
        status_code = 404 if (data == errors.E['clients_id_not_found']) else 400
        err = responses.format_error(data, "invalid client")
        return responses.failure(err, status_code=status_code)


@router.get("/clients", response_model=ClientOut,
            dependencies=[Depends(authorizations.super_admins)])
async def get_all_clients(ctx: RequestContext = Depends()):
    found, data = await clients.view_all_clients(ctx)
    if found:
        resp = [ClientOut.from_client(c) for c in data]
        return responses.success(resp)
    else:
        status_code = 404 if (data == errors.E['clients_field_empty']) else 400
        err = responses.format_error(data, "no clients available")
        return responses.failure(err, status_code=status_code)


@router.post("/clients/{client_id}/flags", response_model=ClientFlagsOut,
             dependencies=[Depends(authorizations.super_admins)])
async def set_client_flags(client_id: int, args: ClientFlagsIn, ctx: RequestContext = Depends()):
    res, data = await clients.set_client_flags(ctx,
                                               client_id,
                                               args.corp_load,
                                               args.rbc_bill_payment,
                                               args.load_hub,
                                               args.pad,
                                               args.eft,
                                               args.ach,
                                               args.card_to_card,
                                               args.e_transfer,
                                               args.bill_payment,
                                               args.bank_to_card,
                                               args.card_to_bank,
                                               args.eft_app,
                                               args.ach_app)
    
    if res:
        resp = ClientFlagsOut.from_flag(data)
        return responses.success(resp)
    
    err = responses.format_error(data, 'unable to set flags')
    return responses.failure(err)


@router.get("/clients/{client_id}/flags", response_model=ClientFlagsOut,
            dependencies=[Depends(authorizations.super_admins)])
async def view_client_flags(client_id: int, ctx: RequestContext = Depends()):
    res, data = await clients.view_client_flags(ctx, client_id)

    if res:
        resp = ClientFlagsOut.from_flag(data)
        return responses.success(resp)
    
    err = responses.format_error(data, 'unable to view flags')
    return responses.failure(err)


@router.post("/clients/{client_id}/file-card-proxies",
            dependencies=[Depends(authorizations.super_admins)])
async def add_card_proxies(client_id: int, proxy_file: UploadFile = File(...),
                            ctx: RequestContext = Depends()):
    file_name = f"{client_id}_card_proxies.csv"
    path_name = "/tmp/{}".format(file_name)
    destination = Path(path_name)
    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(proxy_file.file, buffer)

    finally:
        _ = await proxy_file.close()

    # process the file.
    ok, added, not_added = await clients.add_proxies_from_file(ctx, client_id, path_name)
    
    resp = {
        'status': ok,
        'added': len(added),
        'added_details': added,
        'not_added': len(not_added),
        'not_added_details': not_added
    }
    return responses.success(resp)


@router.delete("/clients/{client_id}", response_model=ClientOut,
               dependencies=[Depends(authorizations.super_admins)])
async def delete_client(client_id: int, ctx: RequestContext = Depends()):
    found, data = await clients.deactivate(ctx, client_id)
    if found:
        resp = ClientOut.from_client(data)
        return responses.success(resp)
    else:
        status_code = 404 if (data == errors.E['clients_id_not_found']) else 400
        err = responses.format_error(data, "invalid member")
        return responses.failure(err, status_code=status_code)


