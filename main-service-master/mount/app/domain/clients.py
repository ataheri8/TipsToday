"""Module for handling all the repo functionality for clients"""
from dataclasses import dataclass
import uuid

from app.common import logger
from app.common import json as json_util
from app.common import security as sek

from app.domain import DBQueryExecutor, BaseRepo


@dataclass(frozen=True)
class Client:
    client_id: int
    status: str
    client_name: str
    company_name: str
    program_id: int
    terms_conditions: str
    csr_instructions: str
    email_alert_address: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_record(rec):
        return Client(
            client_id=rec.get('client_id'),
            status=rec.get('client_status'),
            client_name=rec.get('client_name'),
            company_name=rec.get('company_name'),
            program_id=rec.get('program_id'),
            terms_conditions=rec.get('terms_conditions'),
            csr_instructions=rec.get('csr_instructions'),
            email_alert_address=rec.get('email_alert_address'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at')
        )


@dataclass(frozen=True)
class ClientFlag:
    flag_id: int
    client_id: int
    corp_load: int
    rbc_bill_payment: int
    load_hub: int
    pad: int
    eft: int
    ach: int
    card_to_card: int
    e_transfer: int
    bill_payment: int
    bank_to_card: int
    card_to_bank: int
    eft_app: int
    ach_app: int
    created_at: str
    updated_at: str

    @staticmethod
    def from_record(rec):
        return ClientFlag(
            flag_id=rec.get('flag_id'),
            client_id=rec.get('client_id'),
            corp_load=rec.get('corp_load'),
            rbc_bill_payment=rec.get('rbc_bill_payment'),
            load_hub=rec.get('load_hub'),
            pad=rec.get('pad'),
            eft=rec.get('eft'),
            ach=rec.get('ach'),
            card_to_card=rec.get('card_to_card'),
            e_transfer=rec.get('e_transfer'),
            bill_payment=rec.get('bill_payment'),
            bank_to_card=rec.get('bank_to_card'),
            card_to_bank=rec.get('card_to_bank'),
            eft_app=rec.get('eft_app'),
            ach_app=rec.get('ach_app'),
            updated_at=rec.get('updated_at'),
            created_at=rec.get('created_at'),
        )


CLIENT_ACTIVE_STATUS = "active"
CLIENT_INACTIVE_STATUS = "inactive"


class ClientsRepo(BaseRepo):

    READ_PARAMS = """client_id, client_status, client_name, company_name, program_id,
                     terms_conditions, csr_instructions, email_alert_address,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def create(self, client_name, company_name, program_id, terms, csr_info, email_alert,
                     client_status=CLIENT_ACTIVE_STATUS):
        sql = f"""INSERT INTO clients (client_status, client_name, company_name, program_id,
                                       terms_conditions, csr_instructions, email_alert_address)
                       VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING {self.READ_PARAMS}"""

        rec = await self.db.exec_write(sql, client_status, client_name, company_name, program_id,
                                       terms, csr_info, email_alert)
        return rec


    async def bulk_transfer(self, client_id, mobile, employee_id, first, last, amount):
        sql = f"""INSERT INTO customer_card_info (client_id, mobile, employee_id, first, last, amount)
                                VALUES ($1, $2, $3, $4, $5, $6)
                             RETURNING {self.READ_PARAMS}"""

        params = [client_id, mobile, employee_id, first, last, amount]
        rec = await self.db.exec_write(sql, *params)

        return rec

    async def mark_client_inactive(self, client_id):
        sql = f"""UPDATE clients
                     SET client_status = $2
                   WHERE client_id = $1
               RETURNING {self.READ_PARAMS}"""

        params = [client_id, CLIENT_INACTIVE_STATUS]
        rec = await self.db.exec_write(sql, *params)
        return rec

    async def activate_card(self, client_id, proxy):
        sql = f"""UPDATE customer_card_info
                     SET proxy = $2
                   WHERE client_id = $1
               RETURNING {self.READ_PARAMS}"""

        params = [client_id, proxy]
        rec = await self.db.exec_write(sql, *params)
        return rec
    #
    # reads
    #
    async def get_by_client_id(self, client_id):
        sql = self._base_read() + """ WHERE client_id = $1"""
        rec = await self.db.exec_read(sql, client_id, only_one=True)

        return rec

    async def get_all(self):
        sql = self._base_read()
        rec = await self.db.exec_read(sql)

        return rec

    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM clients"""
        return sql


class ClientFlagsRepo(BaseRepo):

    READ_PARAMS = """flag_id, client_id, corp_load, rbc_bill_payment, load_hub, pad, eft, ach, ach_app,
                     card_to_card, e_transfer, bill_payment, bank_to_card, card_to_bank, eft_app,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db


    #
    # writes
    #
    async def add_flags(self, client_id, corp_load, rbc_bill_pay, load_hub, pad, eft, ach,
                        card_to_card, e_transfer, bill_pay, bank_to_card, card_to_bank, eft_app, ach_app):
        sql = f"""INSERT INTO client_flags (client_id, corp_load, rbc_bill_payment, load_hub, pad,
                                            eft, ach, card_to_card, e_transfer, bill_payment,
                                            bank_to_card, card_to_bank, eft_app, ach_app)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, client_id, corp_load, rbc_bill_pay, load_hub, pad, eft,
                                       ach, card_to_card, e_transfer, bill_pay, bank_to_card,
                                       card_to_bank, eft_app, ach_app)
        return rec
    

    async def update_flags(self, flag_id, client_id, corp_load, rbc_bill_pay, load_hub, pad, eft, ach,
                        card_to_card, e_transfer, bill_pay, bank_to_card, card_to_bank, eft_app, ach_app):
        sql = f"""UPDATE client_flags
                     SET corp_load = $3,
                         rbc_bill_payment = $4,
                         load_hub = $5,
                         pad = $6,
                         eft = $7,
                         ach = $8,
                         card_to_card = $9,
                         e_transfer = $10,
                         bill_payment = $11,
                         bank_to_card = $12,
                         card_to_bank = $13,
                         eft_app = $14,
                         ach_app = $15
                   WHERE flag_id = $1
                     AND client_id = $2
               RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, flag_id, client_id, corp_load, rbc_bill_pay, load_hub, pad,
                                       eft, ach, card_to_card, e_transfer, bill_pay, bank_to_card,
                                       card_to_bank, eft_app, ach_app)
        return rec

    #
    # reads
    #
    async def get_by_client_id(self, client_id):
        sql = self._base_read() + """ WHERE client_id = $1"""

        rec = await self.db.exec_read(sql, client_id, only_one=True)
        return rec

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                    FROM client_flags"""
        return sql
