"""Module for handling all the repo functionality for card proxies"""
from dataclasses import dataclass
import uuid

from app.common import logger
from app.common import json as json_util
from app.common import security as sek

from app.domain import DBQueryExecutor, BaseRepo


@dataclass(frozen=True)
class CardProxy:
    proxy_id: int
    client_id: int
    proxy: str
    proxy_status: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_record(rec):
        return CardProxy(
            id=rec['rec_id'],
            client_id=rec['client_id'],
            proxy=rec['proxy'],
            proxy_status=rec['proxy_status'],
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at')
        )

@dataclass(frozen=True)
class CustomerCardProxy:
    proxy_id: int
    customer_id: int
    proxy: str
    proxy_status: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_record(rec):
        return CustomerCardProxy(
            proxy_id=rec['rec_id'],
            customer_id=rec['customer_id'],
            proxy=rec['proxy'],
            proxy_status=rec['proxy_status'],
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at')
        )


PROXY_STATUS_AVAILABLE = 'available'
PROXY_STATUS_ASSIGNED = 'assigned'
PROXY_STATUS_DISABLED = 'disabled'

CARD_STATUS_ACTIVE = 'active'
CARD_STATUS_SUSPENDED = 'suspended'
CARD_STATUS_DISABLED = 'disabled'

class CustomerCardProxiesRepo(BaseRepo):

    READ_PARAMS = """rec_id, customer_id, proxy, proxy_status, person_id,
                     last4, expiry,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db
    

    #
    # writes
    #
    async def create(self, customer_id, proxy, person_id, status=CARD_STATUS_ACTIVE,
                     last4='', expiry=''):
        sql = f"""INSERT INTO customer_card_proxies (customer_id, proxy,
                                                     proxy_status, person_id,
                                                     last4, expiry)
                       VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql,
                                       customer_id,
                                       proxy,
                                       status,
                                       person_id,
                                       last4,
                                       expiry)
        return rec

    async def change_status(self, status, proxy):
        sql = f"""UPDATE customer_card_proxies
                     SET proxy_status = $1
                   WHERE proxy = $2 

                    RETURNING {self.READ_PARAMS}"""

        params = [status, proxy]
        rec = await self.db.exec_write(sql, *params)

        return rec


    #
    # reads
    #
    async def view_customer_proxy(self, customer_id, proxy):
        sql = self._base_read() + """ WHERE customer_id = $1
                                        AND proxy = $2
                                   ORDER BY rec_id DESC
                                      LIMIT 1"""
        rec = await self.db.exec_read(sql, customer_id, proxy, only_one=True)
        return rec


    async def get_customer_active_proxy(self, customer_id):
        sql = self._base_read() + """ WHERE customer_id = $1
                                        AND proxy_status = $2"""
        
        rec = await self.db.exec_read(sql, customer_id, CARD_STATUS_ACTIVE,
                                      only_one=True)
        return rec

    #
    # helpers
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM customer_card_proxies"""
        return sql




class ClientCardProxiesRepo(BaseRepo):

    READ_PARAMS = """rec_id, client_id, proxy, proxy_status,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def create(self, client_id, proxy, status=PROXY_STATUS_AVAILABLE):
        sql = f"""INSERT INTO client_card_proxies (client_id, proxy, proxy_status)
                       VALUES ($1, $2, $3, $4)
                    RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, client_id, proxy, status)
        return rec

    async def change_status(self, status, proxy):
        sql = f"""UPDATE client_card_proxies
                     SET proxy_status = $1
                   WHERE proxy = $2 

                    RETURNING {self.READ_PARAMS}"""

        params = [status, proxy]
        rec = await self.db.exec_write(sql, *params)

        return rec

    #
    # reads
    #
    async def get_by_id(self, proxy_id):
        sql = self._base_read() + """ WHERE rec_id = $1"""
        rec = await self.db.exec_read(sql, proxy_id, only_one=True)

        return rec


    async def get_by_client_id(self, client_id):
        sql = self._base_read() + """ WHERE client_id = $1"""
        rec = await self.db.exec_read(sql, client_id)

        return rec


    async def check_status(self, proxy):
        sql = self._base_read() + """ WHERE proxy = $1 """                                      

        rec = await self.db.exec_read(sql, proxy, only_one=True)

        return rec


    async def get_by_proxy(self, proxy):
        sql = self._base_read() + """ WHERE proxy = $1"""
        rec = await self.db.exec_read(sql, proxy, only_one=True)

        return rec

    
    #
    # helpers
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM client_card_proxies"""
        return sql
