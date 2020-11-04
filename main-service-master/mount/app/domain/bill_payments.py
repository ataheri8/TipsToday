"""Module for handling all the repo functionality for bill payments"""
from dataclasses import dataclass, field
from typing import List

from app.common import logger
from app.common import json as json_util
from app.common import security as sek

from app.domain import DBQueryExecutor, BaseRepo


@dataclass(frozen=True)
class BillPayee:
    payee_id: int
    customer_id: int
    payee_status: str
    payee_name: str
    payee_code: str
    account_number: str
    created_at: str
    updated_at: str
    
    @staticmethod
    def from_record(rec):
        return BillPayee(
            payee_id=rec.get('payee_id'),
            customer_id=rec.get('customer_id'),
            payee_status=rec.get('payee_status'),
            payee_name=rec.get('payee_name'),
            payee_code=rec.get('payee_code'),
            account_number=rec.get('account_number'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at'),
        )    


@dataclass(frozen=True)
class BillPayment:
    payment_amount: float
    payee_name: str
    account_number: str
    submitted_at: str


STATUS_ACTIVE = 'active'
STATUS_INACTIVE = 'inactive'


class BillPayeesRepo(BaseRepo):

    READ_PARAMS = """payee_id, customer_id, payee_status, payee_name, payee_code, account_number,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def create(self, customer_id, payee_name, payee_code, account_number, status=STATUS_ACTIVE):
        sql = f"""INSERT INTO bill_payees (customer_id, payee_status, payee_name, payee_code,
                                           account_number)
                       VALUES ($1, $2, $3, $4, $5)
                    RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, customer_id, status, payee_name, payee_code, account_number)
        
        return rec


    async def change_status(self, payee_id, status):
        sql = f"""UPDATE bill_payees
                     SET payee_status = $2,
                         updated_at = CURRENT_TIMESTAMP
                   WHERE payee_id = $1
               RETURNING {self.READ_PARAMS}"""

        rec = await self.db.exec_write(sql, payee_id, status)

        return rec


    async def update_account_number(self, payee_id, account_number):
        sql = f"""UPDATE bill_payees
                     SET account_number = $2,
                         updated_at = CURRENT_TIMESTAMP
                   WHERE payee_id = $1
               RETURNING {self.READ_PARAMS}"""
        rec = await self.db.exec_write(sql, payee_id, account_number)

        return rec


    #
    # reads
    #
    async def get_by_payee_id(self, payee_id):
        sql = self._base_read() + """ WHERE payee_id = $1"""

        rec = await self.db.exec_read(sql, payee_id, only_one=True)
        return rec

    
    async def get_payee_details(self, customer_id, payee_id):
        sql = self._base_read() + """ WHERE payee_id = $1 AND customer_id = $2"""

        rec = await self.db.exec_read(sql, payee_id, customer_id, only_one=True)

        return rec
    

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM bill_payees"""
        return sql
