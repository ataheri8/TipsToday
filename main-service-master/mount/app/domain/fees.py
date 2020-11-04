"""Module for handling all the repo functionality for stores"""
from dataclasses import dataclass, field
from typing import List

from app.common import logger
from app.common import json as json_util
from app.common import security as sek

from app.domain import DBQueryExecutor, BaseRepo


@dataclass(frozen=True)
class Fee:
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
    def from_record(rec):
        return Fee(
            fee_id=rec.get('fee_id'),
            client_id=rec.get('client_id'),
            event_type=rec.get('event_type'),
            fee_type=rec.get('fee_type'),
            fee_value=rec.get('fee_value'),
            currency_code=rec.get('currency_code'),
            status=rec.get('fee_status'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at'),
        )    


STATUS_ACTIVE = 'active'
STATUS_INACTIVE = 'inactive'

FEE_TYPE_FIXED = 'fixed'
FEE_TYPE_PERCENTAGE = 'percentage'
DEFAULT_CURRENCY_CODE = 'CAD'


class FeesRepo(BaseRepo):

    READ_PARAMS = """fee_id, client_id, event_type, fee_type,
                     fee_value, fee_status, currency_code,     
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def create(self, client_id, event_type, fee_value,
                     fee_type=FEE_TYPE_FIXED,
                     currency_code=DEFAULT_CURRENCY_CODE,
                     status=STATUS_ACTIVE):
        sql = f"""INSERT INTO fees (client_id, event_type, fee_type,
                                    fee_value, fee_status, currency_code)
                       VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, client_id, event_type, fee_type,
                                 fee_value, status, currency_code)
        
        return rec


    async def change_status(self, fee_id, status):
        sql = f"""UPDATE fees
                     SET fee_status = $2
                   WHERE fee_id = $1
               RETURNING {self.READ_PARAMS}"""

        params = [fee_id, status]

        rec = await self.db.exec_write(sql, *params)

        return rec


    #
    # reads
    #
    async def get_by_fee_id(self, fee_id):
        sql = self._base_read() + """ WHERE fee_id = $1"""

        rec = await self.db.exec_read(sql, fee_id, only_one=True)
        return rec

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM fees"""
        return sql
