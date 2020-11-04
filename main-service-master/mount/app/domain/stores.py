"""Module for handling all the repo functionality for stores"""
from dataclasses import dataclass, field
from typing import List

from app.common import logger
from app.common import json as json_util
from app.common import security as sek

from app.domain import DBQueryExecutor, BaseRepo


@dataclass(frozen=True)
class Store:
    store_id: int
    client_id: int
    status: str
    store_name: str
    company_name: str
    card_load_identifier: str
    created_at: str
    updated_at: str
    pad_weekday: int
    admins: list = field(default_factory=list)
    wallets: list = field(default_factory=list)

    @staticmethod
    def from_record(rec, wallets=[]):
        _mans = json_util.parse(rec.get('admins'))
        return Store(
            store_id=rec.get('store_id'),
            status=rec.get('store_status'),
            store_name=rec.get('store_name'),
            company_name=rec.get('company_name'),
            card_load_identifier=rec.get('card_load_identifier'),
            client_id=rec.get('client_id'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at'),
            pad_weekday=rec.get('pad_weekday'),
            admins=_mans['admin_ids'],
            wallets=wallets,
        )


@dataclass(frozen=True)
class StoreAddress:
    address_id: int
    store_id: int
    street: str
    city: str
    region: str
    country: str
    postal_code: str
    created_at: str
    updated_at: str
    address_status: str
    street2: str = ""
    street3: str = ""
    lat: float = None
    lng: float = None

    @staticmethod
    def from_record(rec):
        return StoreAddress(
            address_id=rec.get('address_id'),
            store_id=rec.get('store_id'),
            street=rec.get('street'),
            city=rec.get('city'),
            region=rec.get('region'),
            country=rec.get('country'),
            postal_code=rec.get('postal_code'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at'),
            address_status=rec.get('address_status'),
            street2=rec.get('street2'),
            street3=rec.get('street3'),
            lat=rec.get('lat'),
            lng=rec.get('lng'),
        )


@dataclass(frozen=True)
class StoreBankAccount:
    store_bank_account_id: int
    store_id: int
    store_bank_account_status: str
    transit_number: str
    institution_number: str
    account_number: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_record(rec):
        return StoreBankAccount(
            store_bank_account_id=rec.get('store_bank_account_id'),
            store_id=rec.get('store_id'),
            store_bank_account_status=rec.get('store_bank_account_status'),
            transit_number=rec.get('transit_number'),
            institution_number=rec.get('institution_number'),
            account_number=rec.get('account_number'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at'),
        )


STATUS_ACTIVE = 'active'
STATUS_INACTIVE = 'inactive'


class StoresRepo(BaseRepo):

    READ_PARAMS = """store_id, store_status, store_name, client_id,
                     admins, pad_weekday, company_name, card_load_identifier,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def create(self, store_name, client_id, pad_weekday, company_name, card_load_id, admins,
                     status=STATUS_ACTIVE):
        sql = f"""INSERT INTO stores (store_name, client_id, pad_weekday, company_name,
                                      card_load_identifier, admins, store_status)
                       VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING {self.READ_PARAMS}"""
        _ids = list(map(str, admins))
        _mans = {"admin_ids": _ids}
        _admins = json_util.stringify(_mans)

        params = [store_name, client_id, pad_weekday, company_name, card_load_id, _admins, status]

        rec = await self.db.exec_write(sql, *params)

        return rec

    async def change_status(self, store_id, status):
        sql = f"""UPDATE stores
                     SET store_status = $2
                   WHERE store_id = $1
               RETURNING {self.READ_PARAMS}"""

        params = [store_id, status]

        rec = await self.db.exec_write(sql, *params)

        return rec

    #
    # reads
    #
    async def get_by_store_id(self, store_id):
        sql = self._base_read() + """ WHERE store_id = $1"""

        rec = await self.db.exec_read(sql, store_id, only_one=True)
        return rec

    async def get_by_store_name_and_client_id(self, store_name, client_id):
        sql = self._base_read() + """ WHERE store_name = $1 AND client_id = $2"""
        rec = await self.db.exec_read(sql, store_name, client_id, only_one=True)

        return rec

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM stores"""
        return sql


class AddressesRepo(BaseRepo):

    READ_PARAMS = """address_id, store_id, street, street2, street3, city, region, country,
                     postal_code, address_status, lat, lng,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db


    #
    # writes
    #
    async def add_address(self, store_id, street, city, region, country, postal_code,
                          street2=None, street3=None, lat=None, lng=None, status=STATUS_ACTIVE):
        sql = f"""INSERT INTO store_addresses (store_id, street, city,
                                               region, country, postal_code,
                                               address_status, street2, street3, lat, lng)
                      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                   RETURNING {self.READ_PARAMS}"""

        rec = await self.db.exec_write(sql, store_id, street, city, region,
                                       country, postal_code, status, street2,
                                       street3, lat, lng)

        return rec


    #
    # reads
    #
    async def get_by_store_id(self, store_id):
        sql = self._base_read() + """ WHERE store_id = $1"""

        recs = await self.db.exec_read(sql, store_id)
        return recs

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                    FROM store_addresses"""
        return sql


class StoreBankAccountsRepo(BaseRepo):

    READ_PARAMS = """store_bank_account_id, store_id, store_bank_account_status, transit_number,
                     institution_number, account_number,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db


    #
    # writes
    #
    async def add_bank_account(self, store_id, transit_number, institution_number, account_number):
        sql = f"""INSERT INTO store_bank_accounts(store_id, store_bank_account_status, transit_number,
                                                  institution_number, account_number)
                       VALUES ($1, $2, $3, $4, $5)
                    RETURNING {self.READ_PARAMS}"""

        rec = await self.db.exec_write(sql, store_id, STATUS_ACTIVE, transit_number,
                                       institution_number, account_number)

        return rec


    async def update_bank_account(self, store_id, bank_account_id, transit_num, inst_num, account_num):
        sql = f"""UPDATE store_bank_accounts
                     SET transit_number = $3,
                         institution_number = $4,
                         account_number = $5,
                         updated_at = CURRENT_TIMESTAMP
                   WHERE store_id = $2
                     AND store_bank_account_id = $1
               RETURNING {self.READ_PARAMS}"""

        rec = await self.db.exec_write(sql, bank_account_id, store_id, transit_num, inst_num, account_num)

        return rec


    #
    # reads
    #
    async def get_by_store_id(self, store_id):
        sql = self._base_read() + """ WHERE store_id = $1"""

        recs = await self.db.exec_read(sql, store_id)
        return recs


    async def get_by_bank_account_id(self, store_id, bank_account_id):
        sql = self._base_read() + """ WHERE store_bank_account_id = $1
                                        AND store_id = $2"""

        rec = await self.db.exec_read(sql, bank_account_id, store_id, only_one=True)
        return rec

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                    FROM store_bank_accounts"""
        return sql
