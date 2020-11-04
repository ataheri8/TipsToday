"""Module for handling all the repo functionality for clients"""
from dataclasses import dataclass
from decimal import Decimal

import arrow

from app.common import logger
from app.common import json as json_util

from app.domain import DBQueryExecutor, BaseRepo


@dataclass(frozen=True)
class Wallet:
    wallet_id: int
    client_id: int
    store_id: int
    status: str
    name: str
    current_amount: float
    alert_amount: float
    created_at: str
    updated_at: str

    @staticmethod
    def from_record(rec):
        return Wallet(
            wallet_id=rec.get('wallet_id', 0),
            client_id=rec.get('client_id'),
            store_id=rec.get('store_id'),
            status=rec.get('wallet_status'),
            name=rec.get('wallet_name'),
            current_amount=rec.get('current_amount'),
            alert_amount=rec.get('alert_amount'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at')
        )


@dataclass(frozen=True)
class WalletActivity:
    rec_id: int
    wallet_id: int
    client_id: int
    store_id: int
    adjustment_amount: float
    previous_amount: float
    total_amount: float
    created_at: str
    adjuster_id: int
    adjuster_type: str

    @staticmethod
    def from_record(rec):
        return WalletActivity(
            rec_id=rec.get('rec_id'),
            wallet_id=rec.get('wallet_id'),
            client_id=rec.get('client_id'),
            store_id=rec.get('store_id'),
            adjustment_amount=rec.get('adjustment_amount'),
            previous_amount=rec.get('previous_amount'),
            total_amount=rec.get('total_amount'),
            created_at=rec.get('created_at'),
            adjuster_id=rec.get('entity_id'),
            adjuster_type=rec.get('entity_type'),
        )


WALLET_ACTIVE_STATUS = "active"
WALLET_INACTIVE_STATUS = "inactive"



def check_balances_against_amount(walls, amount):
    amounts = [w['current_amount'] for w in walls]
    wall_sum = sum(amounts)
    logger.warning("######=====> wall_sum: ", wall_sum=wall_sum)
    if amount > 0:
        new_sum = wall_sum - Decimal(amount)
        return new_sum if new_sum > 0 else None
    
    return True


class WalletsRepo(BaseRepo):

    READ_PARAMS = """wallet_id, store_id, client_id, wallet_status,
                     wallet_name, current_amount, alert_amount,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def add_wallet(self, client_id, store_id, wallet_name, alert_amount,
                         wallet_status=WALLET_ACTIVE_STATUS):
        sql = f"""INSERT INTO wallets (client_id, store_id, wallet_name,
                                       alert_amount, wallet_status)
                       VALUES ($1, $2, $3, $4, $5)
                    RETURNING {self.READ_PARAMS}"""
        params = [client_id, store_id, wallet_name, alert_amount, wallet_status]
        rec = await self.db.exec_write(sql, *params)

        return rec

    async def mark_wallet_inactive(self, wallet_id, client_id):
        sql= f"""UPDATE wallets
                    SET wallet_status = $3
                  WHERE client_id = $2
                    AND wallet_id = $1
              RETURNING {self.READ_PARAMS}"""

        params = [wallet_id, client_id, WALLET_INACTIVE_STATUS]
        rec = await self.db.exec_write(sql, *params)
        return rec


    async def add_wallet_funds(self, wallet_id, amount):
        sql= f"""UPDATE wallets
                    SET current_amount = current_amount + $2
                  WHERE wallet_id = $1
              RETURNING {self.READ_PARAMS}"""

        params = [wallet_id, amount]
        rec = await self.db.exec_write(sql, *params)
        return rec

    
    async def update_amount(self, client_id, wallet_id, amount):
        sql = f"""UPDATE wallets
                     SET current_amount = $3
                   WHERE client_id = $1
                     AND wallet_id = $2
               RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, client_id, wallet_id, amount)
        return rec


    async def decrement(self, wallet_id, amount):
        sql = f"""UPDATE wallets
                     SET current_amount = current_amount - $2
                   WHERE wallet_id = $1
               RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, wallet_id, amount)
        return rec
                

    async def increment(self, wallet_id, amount):
        sql = f"""UPDATE wallets
                     SET current_amount = current_amount + $2
                   WHERE wallet_id = $1
               RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, wallet_id, amount)
        return rec


    #
    # reads
    #
    async def get_by_client_id(self, client_id, active_only=True):
        sql = self._base_read() + """ WHERE client_id = $1"""
        params = [client_id]

        if active_only:
            sql += """ AND wallet_status = $2"""
            params.append(WALLET_ACTIVE_STATUS)
        
        rec = await self.db.exec_read(sql, *params)
        return rec

    async def get_by_store_id(self, store_id, active_only=True):
        sql = self._base_read() + """ WHERE store_id = $1"""
        params = [store_id]

        if active_only:
            sql += """ AND wallet_status = $2"""
            params.append(WALLET_ACTIVE_STATUS)
        
        rec = await self.db.exec_read(sql, *params)
        return rec

    async def get_client_wallet(self, client_id, wallet_id):
        sql = self._base_read() + """ WHERE client_id = $1 AND wallet_id = $2"""
        params = [client_id, wallet_id]

        rec = await self.db.exec_read(sql, *params, only_one=True)
        return rec

    async def get_client_store_wallet(self, client_id, store_id, wallet_id):
        sql = self._base_read() + """ WHERE client_id = $1
                                        AND store_id = $2
                                        AND wallet_id = $3"""
        params = [client_id, store_id, wallet_id]

        rec = await self.db.exec_read(sql, *params, only_one=True)
        return rec

    async def get_by_wallet_id(self, wallet_id):
        sql = self._base_read() + """ WHERE wallet_id = $1"""
        rec = await self.db.exec_read(sql, wallet_id, only_one=True)

        return rec

    async def get_wallet_by_client_id(self, client_id):
        sql = self._base_read() + """ WHERE client_id = $1"""
        rec = await self.db.exec_read(sql, client_id)

        return rec

    #
    # helpers
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM wallets"""
        return sql


class WalletsAuditRepo(BaseRepo):

    READ_PARAMS = """wallet_id, wallet_name, client_id, client_name, store_id, store_name,
                     entity_id, entity_type, entity_name,
                     adjustment_amount, previous_amount, total_amount, 
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def add_entry(self, wallet_id, wallet_name, client_id, client_name, store_id, store_name,
                        entity_id, entity_type, entity_name, prev_amount, adj_amount, new_amount):
        sql = f"""INSERT INTO wallet_adjustments_history (wallet_id,
                                                          wallet_name,
                                                          client_id,
                                                          client_name,
                                                          store_id,
                                                          store_name,
                                                          adjustment_amount,
                                                          previous_amount,
                                                          total_amount,
                                                          entity_id,
                                                          entity_type,
                                                          entity_name)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    RETURNING {self.READ_PARAMS}"""

        rec = await self.db.exec_write(sql, wallet_id, wallet_name, client_id, client_name,
                                       store_id, store_name, adj_amount, prev_amount, new_amount,
                                       entity_id, entity_type, entity_name)
        
        return rec

    #
    # reads
    # 
    async def view_activity(self, wallet_id, store_id, start_date, end_date):
        sql = self._base_read() + """ WHERE wallet_id = $1
                                        AND store_id = $2
                                        AND created_at >= $3
                                        AND created_at <= $4"""        

        params = [wallet_id, store_id, start_date, end_date]
        recs = await self.db.exec_read(sql, *params)

        return recs

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM wallet_adjustments_history"""
        return sql
