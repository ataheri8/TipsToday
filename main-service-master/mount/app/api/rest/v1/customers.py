import decimal
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.common import logger, errors
from app.api.rest import responses, authorizations
from app.usecases import customers, etransfers, bill_payments

from app.services import FIS_Calls, Sanitize_Calls, DC_Bank_Calls


from app.api.rest.context import RequestContext

from app.domain import clients, card_proxies

router = APIRouter()


#
# Inputs
#
class CustomerLogin(BaseModel):
    identifier: str
    passphrase: str


class NewCustomerStoreIn(BaseModel):
    employee_id: str
    store_id: int

# Not extending this off login because passphrase is generated on creation.
class NewCustomerIn(BaseModel):
    identifier: str
    first_name: str
    last_name: str
    stores: List[NewCustomerStoreIn]


class CustomerStoresIn(BaseModel):
    client_id: int
    store_ids: List[int] = []


class CustomerAddressIn(BaseModel):
    street: str
    city: str
    region: str
    country: str
    postal_code: str
    street2: str = ""
    street3: str = ""


class CustomerResetStartIn(BaseModel):
    identifier: str


class CustomersProxyIn(BaseModel):
    proxy: str


class CustomerChangeInfoIn(BaseModel):
    first_name: str
    last_name: str
    person_id: str


class CustomerResetFinishIn(BaseModel):
    token: str
    passphrase: str


class CustomerSecurityIn(BaseModel):
    current_pass: str
    new_pass: str


class CustomerHistoryIn(BaseModel):
    start_date: str = ''
    days: int = 0


class CustomerCardTransfer(BaseModel):
    to_proxy: str
    amount: float


class EtransferRecipientIn(BaseModel):
    name: str
    email: str
    security_question: str
    security_answer: str
    country: str = 'canada'
    region: str = 'ontario'


class EtransferIn(BaseModel):
    recipient_id: int
    amount: float


class BillPayeeIn(BaseModel):
    name: str
    code: str
    account_number: str


class BillPayeeEditIn(BaseModel):
    account_number: str


class BillPaymentIn(BaseModel):
    payee_id: int
    amount: float


#
# Outputs
#
class CardProxy(BaseModel):
    id: int
    proxy: str
    status: str
    created_at: str
    updated_at: str


class ClientCardProxy(CardProxy):
    client_id: int

    @staticmethod
    def from_card_proxy(p):
        return ClientCardProxy(
            id=p.proxy_id,
            client_id=p.client_id,
            proxy=p.proxy,
            status=p.proxy_status,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )


class CustomerCardProxy(CardProxy):
    customer_id: int

    @staticmethod
    def from_card_proxy(p):
        return CustomerCardProxy(
            id=p.proxy_id,
            customer_id=p.customer_id,
            proxy=p.proxy,
            status=p.proxy_status,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )


class CustomerSessionOut(BaseModel):
    customer_id: int
    identifier: str
    status: str
    session_id: str
    john_stewart: str


class CustomerAddressOut(BaseModel):
    address_id: int
    customer_id: int
    status: str
    street: str
    city: str
    region: str
    country: str
    postal_code: str
    created_at: str
    updated_at: str
    street2: str = ""
    street3: str = ""

    @staticmethod
    def from_address(d):
        return CustomerAddressOut(
            address_id=d.address_id,
            customer_id=d.customer_id,
            status=d.status,
            street=d.street,
            city=d.city,
            region=d.region,
            country=d.country,
            postal_code=d.postal_code,
            created_at=d.created_at,
            updated_at=d.updated_at,
            street2=d.street2,
            street3=d.street3,
        )


@router.post("/customers", response_model=customers.CustomerOut)
async def create_customer(args: NewCustomerIn, ctx: RequestContext = Depends()):
    made, data = await customers.create(ctx,
                                        args.identifier,
                                        args.first_name,
                                        args.last_name,
                                        args.stores)

    if made:
        resp = customers.CustomerOut.from_customer(data)
        return responses.success(resp, status_code=201)
    else:
        err = responses.format_error(data, "Unable to create")
        return responses.failure(err)


@router.get("/customers/{customer_id}", dependencies=[Depends(authorizations.customers)])
async def view_customer(customer_id: int, ctx: RequestContext = Depends()):
    got, data = await customers.view_customer(ctx, customer_id)

    if got:
        resp = customers.CustomerOut.from_customer(data)
        return responses.success(resp)
    else:
        err = responses.format_error(data, "unable to view")
        return responses.failure(err, status_code=404)


@router.post("/customers/{customer_id}/editCustomer", dependencies=[Depends(authorizations.customers)])
async def edit_customer(args: CustomerChangeInfoIn, ctx: RequestContext = Depends()):

    p = await FIS_Calls.update_person(args.person_id, args.first_name, args.last_name)
    if True in p:
        resp = customers.CustomerOut.from_customer(data)
        return responses.success(resp, status_code=201)
    else:
        return responses.failure(p, status_code=401)


@router.post("/customers/{customer_id}/security", dependencies=[Depends(authorizations.customers)])
async def update_customer_password(customer_id: int, args: CustomerSecurityIn,
                                   ctx: RequestContext = Depends()):
    updated, data = await customers.update_passphrase(ctx,
                                                      customer_id,
                                                      args.current_pass,
                                                      args.new_pass)

    if updated:

        p, person_id = await FIS_Calls.create_person(data.first_name, data.last_name, "21 test street", "Toronto", "006", 999999999)

        if(p):
            resp = customers.CustomerOut.from_customer(data)
            updated, data = await customers.update_person_id(ctx,
                                                      customer_id,
                                                      person_id)

            if(updated):
                return responses.success(resp, status_code=201)
            else:
                return responses.failure("person_id not updated",status_code=401)
        else:
            return responses.failure(p,status_code=401)

    else:
        err = responses.format_error(data, "Unable to update")
        return responses.failure(err)


@router.post("/customers/{customer_id}/stores", dependencies=[Depends(authorizations.customers)])
async def update_customer_stores(customer_id: int, args: CustomerStoresIn,
                                 ctx: RequestContext = Depends()):
    updated, data = await customers.update_stores(ctx,
                                                  customer_id,
                                                  args.client_id,
                                                  args.stores)
    if updated:
        resp = {'stores': [d['store_id'] for d in data]}
        return responses.success(resp)

    else:
        err = responses.format_error(data, "unable to update stores")
        return responses.failure(err)


@router.post("/customers/{customer_id}/addresses", response_model=CustomerAddressOut,
             dependencies=[Depends(authorizations.customers)])
async def add_customer_address(customer_id: int, args: CustomerAddressIn,
                               ctx: RequestContext = Depends()):
    made, data = await customers.add_customer_address(ctx,
                                                      customer_id,
                                                      args.street,
                                                      args.city,
                                                      args.region,
                                                      args.country,
                                                      args.postal_code,
                                                      street2=args.street2,
                                                      street3=args.street3)

    if made:
        resp = CustomerAddressOut.from_address(data)
        return responses.success(resp, status_code=201)
    else:
        err = responses.format_error(data, "Unable to create")
        return responses.failure(err)


@router.get("/customers/{customer_id}/addresses/{address_id}",
            response_model=CustomerAddressOut,
            dependencies=[Depends(authorizations.customers)])
async def view_customer_address(customer_id: int, address_id: int,
                                ctx: RequestContext = Depends()):
    got, data = await customers.get_customer_address_by_id(ctx, customer_id, address_id)

    if got:
        resp = CustomerAddressOut.from_address(data)
        return responses.success(resp)
    else:
        err = responses.format_error(data, "unable to retrieve")
        return responses.failure(err, status_code=404)


@router.get("/customers/{customer_id}/addresses", response_model=CustomerAddressOut,
            dependencies=[Depends(authorizations.customers)])
async def view_customer_addresses(customer_id: int, ctx: RequestContext = Depends()):
    _, data = await customers.get_customer_addresses(ctx, customer_id)

    resp = [CustomerAddressOut.from_address(d) for d in data]
    return responses.success(resp)


@router.post("/customer-security-find")
async def customer_reset_password_start(args: CustomerResetStartIn,
                                        ctx: RequestContext = Depends()):
    started, data = await customers.start_reset_pass(ctx, args.identifier)

    if not started:
        logger.warning("Unable to start security reset for: ",
                       identifier=args.identifier,
                       error=data)
        data = 0

    # we always show success on this
    resp = {"started": True, "token": data}
    
    return responses.success(resp)


@router.post("/customer-security-found")
async def customer_reset_password_finish(args: CustomerResetFinishIn,
                                         ctx: RequestContext = Depends()):
    updated, data = await customers.finish_reset_pass(ctx, args.token, args.passphrase)

    if updated:
        resp = customers.CustomerOut.from_customer(data)
        return responses.success(resp)
    else:
        err = responses.format_error(data, "Unable to update")
        return responses.failure(err)


@router.post("/customer-sessions", response_model=CustomerSessionOut)
@router.post("/customer-login", response_model=CustomerSessionOut)
async def login_customer(login: CustomerLogin, ctx: RequestContext = Depends()):  
    authed, session_id, sdata = await customers.do_login(ctx,
                                                         login.identifier,
                                                         login.passphrase)

    if authed:
        resp = CustomerSessionOut(customer_id=sdata['customer_id'],
                                  identifier=sdata['identifier'],
                                  status=sdata['customer_status'],
                                  session_id=sdata['honeypot'],
                                  john_stewart=session_id)
        return responses.success(resp, status_code=201)
    
    else:
        err = responses.format_error(sdata, "invalid authorization")
        return responses.failure(err, status_code=401)


@router.delete("/customer-sessions/{session_id}", dependencies=[Depends(authorizations.customers)])
@router.delete("/customer-logout/{session_id}", dependencies=[Depends(authorizations.customers)])
async def logout_customer(session_id: str, ctx: RequestContext = Depends()):
    cleared, data = await customers.do_logout(ctx, session_id)

    if not cleared:
        err = responses.format_error(data, "")
        return responses.failure(err)

    resp = {"session_id": ""}
    return responses.success(resp)


@router.get("/customer-sessions", response_model=CustomerSessionOut,
            dependencies=[Depends(authorizations.customers)])
async def view_customer_session(ctx: RequestContext = Depends()):
    session_id = ctx.session['session_id']
    found, sdata = await customers.view_session(ctx, session_id)

    if not found:
        err = responses.format_error(sdata, "")
        return responses.failure(err)
    
    resp = CustomerSessionOut(customer_id=sdata['customer_id'],
                                identifier=sdata['identifier'],
                                status=sdata['customer_status'],
                                session_id=sdata['honeypot'],
                                john_stewart=session_id)      

    return responses.success(resp)


@router.post("/customers/{customer_id}/activate-card",
             dependencies=[Depends(authorizations.customers)])
async def customer_activate_card(customer_id: int, args: CustomersProxyIn,
                                 ctx: RequestContext = Depends()):

    activated, data = await customers.activate_card(ctx, customer_id, args.proxy)

    if not activated:
        err = responses.format_error(data, "unable to activate card")
        return responses.failure(err)

    else:
        return responses.success(data)    


@router.get("/customers/{customer_id}/proxies",
            response_model=List[ClientCardProxy],
            dependencies=[Depends(authorizations.customers)])
async def view_customer_proxies(customer_id: int,
                                ctx: RequestContext = Depends()):
    found, data = await customers.get_customer_proxies(ctx, customer_id)

    if not found:
        err = responses.format_error(data)
        return responses.failure(err, status_code=404)
    
    resp = [CustomerCardProxy.from_card_proxy(d) for d in data]
    return responses.success(resp)


@router.get("/customers/{customer_id}/proxies/{proxy}")
async def view_customer_proxy(customer_id: int, proxy: str,
                            ctx: RequestContext= Depends()):
    found, data = await customers.get_customer_proxy_details(ctx, customer_id, proxy)
 
    if not found:
        err = responses.format_error(data)
        return responses.failure(err, status_code=404)
    
    resp = CustomerCardProxy.from_card_proxy(data)
    return responses.success(resp)


@router.get("/customers/{customer_id}/proxies/{proxy_id}/status",
            dependencies=[Depends(authorizations.customers)])
async def view_proxy_status(customer_id: int, proxy_id: str,
                            ctx: RequestContext = Depends()):
    found, data = await customers.get_customer_proxy_status(ctx, customer_id, proxy_id)
 
    if not found:
        err = responses.format_error(data)
        return responses.failure(err, status_code=404)
    
    return responses.success(data)


@router.get("/customers/{customer_id}/proxies/{proxy_id}/balance",
            dependencies=[Depends(authorizations.customers)])
async def check_proxy_balance(customer_id: int, proxy_id: str,
                              ctx: RequestContext = Depends()):
    found, data = await customers.get_customer_proxy_balance(ctx,
                                                             customer_id,
                                                             proxy_id)
    if not found:
        err = responses.format_error(data, "unable to view proxy balance")
        return responses.failure(err)    
    else:
        return responses.success(data)    


@router.post("/customers/{customer_id}/card-transfer",
             dependencies=[Depends(authorizations.customers)])
async def customer_card_transfer(customer_id: int, 
                                 args: CustomerCardTransfer,
                                 ctx: RequestContext = Depends()):
    res, data = await customers.card_transfer(ctx,
                                              customer_id,
                                              args.to_proxy,
                                              args.amount)
    
    if not res:
        err = responses.format_error(data, "unable to transfer funds")
        return responses.failure(err)

    else:
        return responses.success(data)    


@router.get("/customers/{customer_id}/transactions",
            dependencies=[Depends(authorizations.customers)])
async def view_customer_transactions(customer_id: int,
                                     ctx: RequestContext = Depends()):

    res, data = await customers.get_transactions(ctx,
                                                 customer_id)
    
    if not res:
        err = responses.format_error(data, "unable to get transactions")
        return responses.failure(err)

    else:
        return responses.success(data)    


#
# etransfers
#
@router.post("/customers/{customer_id}/etransfer-recipients", response_model=etransfers.RecipientOut,
             dependencies=[Depends(authorizations.customers)])
async def customer_add_etransfer_recipient(customer_id: int, args: EtransferRecipientIn,
                                           ctx: RequestContext = Depends()):
    res, data = await etransfers.create_recipient(ctx, customer_id, args.name, args.email, args.security_question,
                                                  args.security_answer)
    
    if not res:
        err = responses.format_error(data, "unable to create recipient")
        return responses.failure(err)

    else:
        resp = etransfers.RecipientOut.from_recipient(data)
        return responses.success(resp)    


@router.get("/customers/{customer_id}/etransfer-recipients", response_model=List[etransfers.RecipientOut],
            dependencies=[Depends(authorizations.customers)])
async def customer_view_recipients(customer_id: int, ctx: RequestContext = Depends()):
    _, data = await etransfers.get_recipients(ctx, customer_id)

    resp = [etransfers.RecipientOut.from_recipient(d) for d in data]
    return responses.success(resp)


@router.get("/customers/{customer_id}/etransfer-recipients/{recipient_id}",
            response_model=etransfers.RecipientOut,
            dependencies=[Depends(authorizations.customers)])
async def customer_view_recipient_details(customer_id: int, recipient_id: int,
                                          ctx: RequestContext = Depends()):
    res, data = await etransfers.get_recipient_details(ctx, customer_id, recipient_id)

    if res:
        resp = etransfers.RecipientOut.from_recipient(data)
        return responses.success(resp)
    
    err = responses.format_error(data, "unable to view recipient")
    return responses.failure(err)


@router.post("/customers/{customer_id}/etransfer-recipients/{recipient_id}",
             response_model=etransfers.RecipientOut,
             dependencies=[Depends(authorizations.customers)])
async def customer_update_etransfer_recipient(customer_id: int, recipient_id: int,
                                              args: EtransferRecipientIn,
                                              ctx: RequestContext = Depends()):
    res, data = await etransfers.update_recipient(ctx, customer_id, recipient_id, args.name,
                                                  args.email, args.security_question,
                                                  args.security_answer)
    if res:
        resp = etransfers.RecipientOut.from_recipient(data)
        return responses.success(resp)
    
    err = responses.format_error(data, "unable to update recipient")
    return responses.failure(err)


@router.delete("/customers/{customer_id}/etransfer-recipients/{recipient_id}",
               response_model=etransfers.RecipientOut,
               dependencies=[Depends(authorizations.customers)])
async def customer_deactivate_etransfer_recipient(customer_id: int, recipient_id: int,
                                                  ctx: RequestContext = Depends()):
    res, data = await etransfers.deactivate_recipient(ctx, customer_id, recipient_id)

    if res:
        resp = etransfers.RecipientOut.from_recipient(data)
        return responses.success(resp)
    
    err = responses.format_error(data, "unable to deactivate recipient")
    return responses.failure(err)



@router.post("/customers/{customer_id}/etransfers", response_model=etransfers.EtransferOut,
             dependencies=[Depends(authorizations.customers)])
async def customer_send_etransfer(customer_id: int, args: EtransferIn, ctx: RequestContext = Depends()):
    res, data = await etransfers.send_etransfer(ctx, customer_id, args.recipient_id, args.amount)

    if res:
        resp = etransfers.EtransferOut.from_etransfer(data)
        return responses.success(resp)

    err = responses.format_error(data, "unable to create etransfer")
    return responses.failure(err)


@router.get("/customers/{customer_id}/etransfers", response_model=List[etransfers.EtransferOut],
            dependencies=[Depends(authorizations.customers)])
async def customer_view_etransfers(customer_id: int, start_date: str = "", end_date: str = "",
                                   ctx: RequestContext = Depends()):
    _, data = await etransfers.get_etransfers(ctx, customer_id, start_date=start_date, end_date=end_date)

    resp = [etransfers.EtransferOut.from_etransfer(d) for d in data]
    return responses.success(resp)


#
# bill payment items
#
@router.get("/customers/{customer_id}/bill-payees-search")
async def customer_bill_payee_search(customer_id: int, token: str = "",
                                     ctx: RequestContext = Depends()):
    res, data = await bill_payments.search_available_payees(ctx, customer_id, token)

    if res:
        return responses.success(data)
    
    else:
        err = responses.format_error(data, 'unable to search payees')
        return responses.failure(data)


@router.post("/customers/{customer_id}/bill-payees", response_model=bill_payments.PayeeOut,
             dependencies=[Depends(authorizations.customers)])
async def customer_add_bill_payee(customer_id: int, args: BillPayeeIn,
                                  ctx: RequestContext = Depends()):
    res, data = await bill_payments.create_payee(ctx, customer_id, args.name, args.code,
                                                 args.account_number)
    
    if not res:
        err = responses.format_error(data, "unable to create payee")
        return responses.failure(err)

    else:
        resp = bill_payments.PayeeOut.from_payee(data)
        return responses.success(resp)    


@router.get("/customers/{customer_id}/bill-payees", response_model=List[bill_payments.PayeeOut],
             dependencies=[Depends(authorizations.customers)])
async def customer_show_bill_payees(customer_id: int, ctx: RequestContext = Depends()):
    res, data = await bill_payments.get_customer_active_payees(ctx, customer_id)

    resp = [bill_payments.PayeeOut.from_payee(d) for d in data]
    return responses.success(resp)


@router.get("/customers/{customer_id}/bill-payees/{payee_id}", response_model=bill_payments.PayeeOut,
             dependencies=[Depends(authorizations.customers)])
async def customer_show_bill_payee_details(customer_id: int, payee_id: int,
                                           ctx: RequestContext = Depends()):
    res, data = await bill_payments.get_payee_details(ctx, customer_id, payee_id)

    resp = bill_payments.PayeeOut.from_payee(data)
    return responses.success(resp)


@router.delete("/customers/{customer_id}/bill-payees/{payee_id}", response_model=bill_payments.PayeeOut,
               dependencies=[Depends(authorizations.customers)])
async def customer_disable_bill_payee(customer_id: int, payee_id: int, ctx: RequestContext = Depends()):
    res, data = await bill_payments.disable_payee(ctx, customer_id, payee_id)

    if not res:
        err = responses.format_error(data, 'unable to disable payee')
        return responses.failure(err)
    
    resp = bill_payments.PayeeOut.from_payee(data)
    return responses.success(resp)


@router.post("/customers/{customer_id}/bill-payees/{payee_id}", response_model=bill_payments.PayeeOut,
             dependencies=[Depends(authorizations.customers)])
async def customer_edit_bill_payee(customer_id: int, payee_id: int, args: BillPayeeEditIn,
                                   ctx: RequestContext = Depends()):
    res, data = await bill_payments.update_payee_account_number(ctx, customer_id, payee_id,
                                                                args.account_number)
    if not res:
        err = responses.format_error(data, 'unable to update payee')
        return responses.failure(err)
    
    resp = bill_payments.PayeeOut.from_payee(data)
    return responses.success(resp)


@router.post("/customers/{customer_id}/bill-payments",
             dependencies=[Depends(authorizations.customers)])
async def customer_create_bill_payment(customer_id: int, args: BillPaymentIn,
                                       ctx: RequestContext = Depends()):
    res, data = await bill_payments.create_bill_payment(ctx, customer_id, args.payee_id, args.amount)

    if not res:
        err = responses.format_error(data, 'unable to create bill payment')
        return responses.failure(err)

    return responses.success(data)
