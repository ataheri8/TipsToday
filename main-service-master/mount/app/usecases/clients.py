import csv

from app.common import logger, errors
from app.usecases.context import Context

from app.domain import clients, card_proxies, programs
from app.common import security as sek
from app.common import json as json_util


# Writes
async def create(ctx: Context, client_name, company_name, program_id, terms_conds, csr_instructions,
                 email_alert_address):
    l_repo = clients.ClientsRepo(ctx.db)
    pg_repo = programs.ProgramsRepo(ctx.db)

    exists = await l_repo.search(client_name=client_name)        

    if exists:
        return False, errors.E['clients_name_exists']

    prog_exists = await pg_repo.get_by_program_id(program_id)

    if not prog_exists:
        return False, errors.E['clients_program_not_found']

    rec = await l_repo.create(client_name, company_name, program_id, terms_conds, csr_instructions,
                              email_alert_address)

    if rec:
        return True, clients.Client.from_record(rec)
    else:
        return False, errors.E['clients_unable_to_create']


async def deactivate(ctx: Context, client_id):
    repo = clients.ClientsRepo(ctx.db)
    exists = await repo.get_by_client_id(client_id)

    if not exists:
        return False, errors.E['clients_id_not_found']
    
    c = await repo.mark_client_inactive(client_id)
    if c:
        return True, clients.Client.from_record(c)
    else:
        return False, errors.E['clients_unable_to_deactivate']


async def add_proxies_from_file(ctx: Context, client_id, file_path):
    repo = card_proxies.ClientCardProxiesRepo(ctx.db)
    added = []
    not_added = []

    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            proxy = f"{row[0]}"
            proxy = clean_card_proxy(proxy)

            if proxy:
                exists = await repo.get_by_proxy(proxy)
                if exists:
                    not_added.append(proxy)
                else:
                    data = await repo.create(client_id, proxy)
                    if not data:
                        not_added.append(proxy)
                    else:
                        added.append(proxy)

    return True, added, not_added


async def set_client_flags(ctx: Context, client_id, corp_load, rbc_bill_payment, load_hub, pad,
                           eft, ach, card_to_card, e_transfer, bill_payment, bank_to_card,
                           card_to_bank, eft_app, ach_app):
    cf_repo = clients.ClientFlagsRepo(ctx.db)

    exists = await cf_repo.get_by_client_id(client_id)

    if exists:
        # we are updating
        rec = await cf_repo.update_flags(exists['flag_id'], client_id, corp_load, rbc_bill_payment,
                                         load_hub, pad, eft, ach, card_to_card, e_transfer,
                                         bill_payment, bank_to_card, card_to_bank, eft_app, ach_app)
    else:
        # set new
        rec = await cf_repo.add_flags(client_id, corp_load, rbc_bill_payment, load_hub, pad, eft, ach,
                                      card_to_card, e_transfer, bill_payment, bank_to_card, card_to_bank,
                                      eft_app, ach_app)
    
    if rec:
        return True, clients.ClientFlag.from_record(rec)
    else:
        return False, errors.E['clients_unable_to_set_flags']


async def view_client_flags(ctx: Context, client_id):
    cf_repo = clients.ClientFlagsRepo(ctx.db)

    rec = await cf_repo.get_by_client_id(client_id)

    if rec:
        return True, clients.ClientFlag.from_record(rec)
    else:
        return False, errors.E['clients_flags_not_found']


# Reads
async def find_by_program_name(ctx: Context, program_name: str):
    repo = clients.ClientsRepo(ctx.db)
    cust = await repo.get_by_program_name(program_name)

    if cust:
        return True, clients.Client.from_record(cust)
    else:
        return False, errors.E['clients_program_not_found']


async def find_by_id(ctx: Context, client_id: int):
    repo = clients.ClientsRepo(ctx.db)
    cust = await repo.get_by_client_id(client_id)

    if cust:
        return True, clients.Client.from_record(cust)
    else:
        return False, errors.E['clients_id_not_found']



async def view_all_clients(ctx: Context):
    repo = clients.ClientsRepo(ctx.db)
    cust = await repo.get_all_client_ids()

    if len(cust) != 0:
        return True, clients.Client
    else:
        return False, errors.E['clients_field_empty']


async def create_customer(ctx: Context, employee_id, client_id, first, last, mobile,
                              address, city, province, postal_code, temp_pass):
    repo = clients.ClientsRepo(ctx.db)
    exists = await repo.get_by_client_id(client_id)

    if not exists:
        return False, errors.E('clients_id_not_found')

    c = await repo.create_customer(employee_id, client_id, first, last, mobile,
                              address, city, province, postal_code, temp_pass)

    if c:
        return True, clients.Client.from_record(c)
    else:
        return False, errors.E('customer_unable_to_create')


async def bulk_transfer(ctx: Context, client_id, mobile, employee_id, first, last, amount):
    repo = clients.ClientsRepo(ctx.db)
    cust = await repo.bulk_transfer(client_id, mobile, employee_id, first, last, amount)

    if cust:
        return True, clients.Client.from_record(cust)
    else:
        return False, errors.E('customer_not_found')


async def get_all(ctx: Context):
    repo = clients.ClientsRepo(ctx.db)

    _clients = await repo.get_all()
    found = [clients.Client.from_record(d) for d in _clients]

    return True, found




#
# Helpers
#
def clean_card_proxy(proxy):
    val = proxy.strip().lower()
    return val

