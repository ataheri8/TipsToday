"""Module for handling all the repo functionality for stores"""
from dataclasses import dataclass, field
from typing import List
import uuid

from app.common import logger
from app.common import json as json_util
from app.common import security as sek

from app.domain import DBQueryExecutor, BaseRepo


@dataclass(frozen=True)
class PayoutTxn:
    rec_id: int
    txn_id: str
    customer_id: int
    proxy: str
    entity_id: int
    entity_type: str
    event_type: str
    currency_code: str
    txn_amount: float
    txn_status: str
    created_at: str
    description: str = ''
    
    @staticmethod
    def from_record(rec):
        return PayoutTxn(
            rec_id=rec.get('rec_id'),
            txn_id=rec.get('txn_id'),
            customer_id=rec.get('customer_id'),
            proxy=rec.get('proxy'),
            entity_id=rec.get('entity_id'),
            entity_type=rec.get('entity_type'),
            event_type=rec.get('event_type'),
            currency_code=rec.get('currency_code'),
            txn_amount=float(rec.get('txn_amount')),
            txn_status=rec.get('txn_status'),
            created_at=rec.get('created_at'),
            description=rec.get('description')
        )


def generate_txn_id():
    return '{}'.format(uuid.uuid4())


class TxnsRepo(BaseRepo):

    READ_PARAMS = """rec_id, txn_id, customer_id, proxy, entity_id,
                     entity_type, event_type, currency_code, txn_amount,
                     txn_status, description,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def create_payout(self, txn_id, customer_id, proxy, entity_id,
                            entity_type, event_type, txn_amount, txn_status,
                            currency_code, description=''):
        return await self._add_entry(txn_id, customer_id, proxy, entity_id,
                                     entity_type, event_type, txn_amount,
                                     txn_status, currency_code, description)


    async def complete_payout(self, txn_id, entity_id, entity_type, txn_status):
        recs = await self.get_by_txn_id(txn_id)
        logger.warning("recs are: ---> ", recs=recs)

        # get the last record
        r = recs[-1]
        logger.warning("*****>>>> r ---> ", r=r)
        return await self._add_entry(txn_id, r['customer_id'], r['proxy'], entity_id,
                                     entity_type, r['event_type'], r['txn_amount'],
                                     txn_status, r['currency_code'], r['description'])


    async def _add_entry(self, txn_id, customer_id, proxy, entity_id, entity_type,
                         event_type, txn_amount, txn_status, currency_code, description):
        sql = f"""INSERT INTO transactions (txn_id, customer_id, proxy,
                                            txn_amount, txn_status, entity_id,
                                            entity_type, event_type, currency_code,
                                            description)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, txn_id, customer_id, proxy, txn_amount,
                                       txn_status, entity_id, entity_type,
                                       event_type, currency_code, description)
        return rec
        

    #
    # reads
    #
    async def get_by_txn_id(self, txn_id):
        sql = self._base_read() + """ WHERE txn_id = $1"""

        recs = await self.db.exec_read(sql, txn_id)
        return recs

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM transactions"""
        return sql
