"""Module for handling all the repo functionality for admins"""
import re
import uuid
from dataclasses import dataclass, field
from typing import List

from app.common import logger
from app.common import json as json_util
from app.common import security as sek

from app.domain import DBQueryExecutor, BaseRepo


@dataclass(frozen=True)
class Customer:
    customer_id: int
    customer_status: str
    first_name: str
    last_name: str
    identifier: str
    created_at: str
    updated_at: str
    store_ids: list = field(default_factory=list)

    @staticmethod
    def from_record(rec, store_ids=[]):
        return Customer(
            customer_id=rec.get('customer_id'),
            customer_status=rec.get('customer_status'),
            first_name=rec.get('first_name'),
            last_name=rec.get('last_name'),
            identifier=rec.get('identifier'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at'),
            store_ids=store_ids,
        )


@dataclass(frozen=True)
class Address:
    address_id: int
    customer_id: int
    street: str
    city: str
    region: str
    country: str
    postal_code: str
    status: str
    created_at: str
    updated_at: str
    street2: str = ""
    street3: str = ""

    @staticmethod
    def from_record(rec):
        return Address(
            address_id=rec.get('address_id'),
            customer_id=rec.get('customer_id'),
            street=rec.get('street'),
            city=rec.get('city'),
            region=rec.get('region'),
            country=rec.get('country'),
            postal_code=rec.get('postal_code'),
            status=rec.get('address_status'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at'),
            street2=rec.get('street2'),
            street3=rec.get('street3'),
        )


STATUS_ACTIVE = 'active'
STATUS_INACTIVE = 'inactive'


def clean_phone_number(phone):
    p = re.sub("\D", "", phone)
    return p


class CustomersRepo(BaseRepo):

    READ_PARAMS = """customer_id, identifier, passphrase, first_name, last_name, customer_status,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def create(self, identifier, passphrase, first_name, last_name):
        sql = f"""INSERT INTO customers (identifier, passphrase, first_name, last_name,
                                         customer_status)
                       VALUES ($1, $2, $3, $4, $5)
                    RETURNING {self.READ_PARAMS}"""

        _phrase = passphrase.strip()
        _pass = sek.get_hashword(passphrase)

        rec = await self.db.exec_write(sql, identifier, _pass, first_name, last_name, STATUS_INACTIVE)
        return rec


    async def change_status(self, customer_id, status):
        sql = f"""UPDATE customers
                     SET customer_status = $2
                   WHERE customer_id = $1
               RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, customer_id, status)

        return rec


    async def update_passphrase(self, customer_id, passphrase):
        sql = f"""UPDATE customers
                     SET passphrase = $2
                   WHERE customer_id = $1
               RETURNING {self.READ_PARAMS}"""

        _phrase = passphrase.strip()
        _pass = sek.get_hashword(passphrase)

        rec = await self.db.exec_write(sql, customer_id, _pass)
        return rec

    
    #
    # reads
    #
    async def get_by_identifier(self, identifier):
        sql = self._base_read() + """ WHERE identifier = $1"""

        rec = await self.db.exec_read(sql, identifier, only_one=True)
        return rec or None


    async def get_by_customer_id(self, customer_id):
        sql = self._base_read() + """ WHERE customer_id = $1"""

        rec = await self.db.exec_read(sql, customer_id, only_one=True)
        return rec or None

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM customers"""
        return sql


class CustomersMappingRepo(BaseRepo):

    READ_PARAMS = """rec_id, client_id, store_id, customer_id, employee_id, map_status,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db


    #
    # writes
    #
    async def add_mapping(self, client_id, store_id, customer_id, employee_id, status=STATUS_ACTIVE):
        sql = f"""INSERT INTO customers_mapping (client_id, store_id, customer_id, employee_id,
                                                 map_status)
                       VALUES ($1, $2, $3, $4, $5)
                    RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, client_id, store_id, customer_id, employee_id, status)
        
        return rec

    
    async def remove_mappings(self, customer_id, client_id, store_id):
        sql = f"""DELETE FROM customers_mapping
                        WHERE client_id = $1
                          AND customer_id = $2
                          AND store_id = $3"""
        
        rec = await self.db.exec_write(sql, client_id, customer_id, store_id)
        return rec


    #
    # reads
    #
    async def get_by_customer_id(self, customer_id):
        sql = self._base_read() + """ WHERE customer_id = $1"""

        recs = await self.db.exec_read(sql, customer_id)
        return recs

    
    async def get_by_store_id(self, store_id):
        sql = self._base_read() + """ WHERE store_id = $1"""

        recs = await self.db.exec_read(sql, store_id)
        return recs


    async def check_employee_exists(self, client_id, employee_id, store_id):
        sql = self._base_read() + f""" WHERE client_id = $1
                                         AND employee_id = $2
                                         AND store_id = $3"""
        
        recs = await self.db.exec_read(sql, client_id, employee_id, store_id)
        return recs

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM customers_mapping"""
        return sql


class AddressesRepo(BaseRepo):

    READ_PARAMS = """address_id, customer_id, street, street2, street3,
                     city, region, country, postal_code, address_status,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db


    #
    # writes
    #
    async def add_address(self, customer_id, street, city, region, country,
                          postal_code, street2=None, street3=None,
                          status=STATUS_ACTIVE):
        sql = f"""INSERT INTO customer_addresses (customer_id, street, city,
                                                  region, country, postal_code,
                                                  address_status, street2, street3)
                      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                   RETURNING {self.READ_PARAMS}"""

        rec = await self.db.exec_write(sql, customer_id, street, city, region,
                                       country, postal_code, status, street2,
                                       street3)
        
        return rec


    #
    # reads
    #
    async def get_by_customer_id(self, customer_id):
        sql = self._base_read() + """ WHERE customer_id = $1"""

        recs = await self.db.exec_read(sql, customer_id)
        return recs

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM customer_addresses"""
        return sql
