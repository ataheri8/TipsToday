"""Module for handling all the repo functionality for admins"""
from dataclasses import dataclass
import uuid

from app.common import logger
from app.common import json as json_util
from app.common import security as sek

from app.domain import DBQueryExecutor, BaseRepo


@dataclass(frozen=True)
class Admin:
    admin_id: int
    status: str
    level: str
    first_name: str
    last_name: str
    identifier: str
    client_id: int
    created_at: str
    updated_at: str
    title: str = ""

    @staticmethod
    def from_record(rec):
        return Admin(
            admin_id=rec.get('admin_id'),
            status=rec.get('admin_status'),
            level=rec.get('level'),
            first_name=rec.get('first_name'),
            last_name=rec.get('last_name'),
            identifier=rec.get('identifier'),
            client_id=rec.get('client_id'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at'),
            title=rec.get('title'),           
        )


STATUS_ACTIVE = 'active'
STATUS_INACTIVE = 'inactive'

LEVEL_STORE = 'store'
LEVEL_COMPANY = 'company'


class AdminsRepo(BaseRepo):

    READ_PARAMS = """admin_id, identifier, passphrase, first_name, last_name,
                     admin_status, client_id, title, level,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def create(self, identifier, passphrase, first_name, last_name, client_id,
                     level, title=""):
        sql = f"""INSERT INTO admins (identifier, passphrase, first_name,
                                      last_name, admin_status, client_id,
                                      level, title)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING {self.READ_PARAMS}"""

        _phrase = passphrase.strip()
        _pass = sek.get_hashword(_phrase)

        params = [identifier, _pass, first_name, last_name, STATUS_ACTIVE,
                  client_id, level, title]

        rec = await self.db.exec_write(sql, *params)

        return rec


    async def change_status(self, admin_id, status):
        sql = f"""UPDATE admins
                     SET admin_status = $2
                   WHERE admin_id = $1
               RETURNING {self.READ_PARAMS}"""

        rec = await self.db.exec_write(sql, admin_id, status)

        return rec


    #
    # reads
    #
    async def get_by_identifier(self, identifier):
        sql = self._base_read() + """ WHERE identifier = $1"""

        rec = await self.db.exec_read(sql, identifier, only_one=True)
        return rec

    async def get_by_admin_id(self, admin_id):
        sql = self._base_read() + """ WHERE admin_id = $1"""

        rec = await self.db.exec_read(sql, admin_id, only_one=True)
        return rec

    async def get_all_admins(self, client_id):
        sql = self._base_read() + """ WHERE client_id = $1"""

        rec = await self.db.exec_read(sql, client_id)
        return rec


    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM admins"""
        return sql


