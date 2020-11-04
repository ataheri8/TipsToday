"""Module for handling all the repo functionality for admins"""
from dataclasses import dataclass
import uuid

from app.common import logger
from app.common import json as json_util
from app.common import security as sek

from app.domain import DBQueryExecutor, BaseRepo


@dataclass(frozen=True)
class SuperAdmin:
    super_admin_id: int
    status: str
    first_name: str
    last_name: str
    identifier: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_record(rec):
        return SuperAdmin(
            super_admin_id=rec.get('super_admin_id'),
            status=rec.get('super_admin_status'),
            first_name=rec.get('first_name'),
            last_name=rec.get('last_name'),
            identifier=rec.get('identifier'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at')
        )

# Constants
STATUS_ACTIVE = 'active'
STATUS_INACTIVE = 'inactive'


class SuperAdminsRepo(BaseRepo):

    READ_PARAMS = """super_admin_id, identifier, passphrase, first_name, last_name,
                     super_admin_status,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def create(self, identifier, passphrase, first_name, last_name):
        sql = f"""INSERT INTO super_admins (identifier, passphrase, first_name,
                                            last_name, super_admin_status)
                       VALUES ($1, $2, $3, $4, $5)
                    RETURNING {self.READ_PARAMS}"""

        _phrase = passphrase.strip()
        _pass = sek.get_hashword(_phrase)

        params = [identifier, _pass, first_name, last_name, STATUS_ACTIVE]

        rec = await self.db.exec_write(sql, *params)

        return rec
    

    async def change_status(self, super_admin_id, status):
        sql = f"""UPDATE super_admins
                     SET super_admin_status = $2
                   WHERE super_admin_id = $1
               RETURNING {self.READ_PARAMS}"""
        
        params = [super_admin_id, status]

        rec = await self.db.exec_write(sql, *params)

        return rec

    
    #
    # reads
    #
    async def get_by_identifier(self, identifier):
        sql = self._base_read() + """ WHERE identifier = $1"""

        rec = await self.db.exec_read(sql, identifier, only_one=True)
        return rec


    async def get_by_super_admin_id(self, super_admin_id):
        sql = self._base_read() + """ WHERE super_admin_id = $1"""

        rec = await self.db.exec_read(sql, super_admin_id, only_one=True)
        return rec


    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM super_admins"""
        return sql
