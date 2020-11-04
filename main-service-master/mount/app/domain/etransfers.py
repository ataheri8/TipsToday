"""Module for handling all the repo functionality for stores"""
from dataclasses import dataclass, field
from typing import List

from app.common import logger
from app.common import json as json_util
from app.common import security as sek

from app.domain import DBQueryExecutor, BaseRepo


@dataclass(frozen=True)
class EtransferRecipient:
    recipient_id: int
    customer_id: int
    recipient_name: str
    email_address: str
    security_question: str
    security_answer: str
    recipient_status: str
    created_at: str
    updated_at: str
    
    @staticmethod
    def from_record(rec):
        return EtransferRecipient(
            recipient_id=rec.get('recipient_id'),
            customer_id=rec.get('customer_id'),
            recipient_name=rec.get('recipient_name'),
            email_address=rec.get('email_address'),
            security_question=rec.get('security_question'),
            security_answer=rec.get('security_answer'),
            recipient_status=rec.get('recipient_status'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at'),
        )    


@dataclass(frozen=True)
class Etransfer:
    amount: float
    fee_amount: float
    recipient_name: str
    submitted_at: str
    transaction_id: str

    @staticmethod
    def from_record(rec):
        return Etransfer(
            amount=rec.get('etransfer_amount'),
            fee_amount=rec.get('fee_amount'),
            recipient_name=rec.get('recipient_name'),
            submitted_at=rec.get('created_at'),
            transaction_id=rec.get('etransfer_id'),
        )


STATUS_ACTIVE = 'active'
STATUS_INACTIVE = 'inactive'


class EtransfersRepo(BaseRepo):

    READ_PARAMS = """rec_id, customer_id, etransfer_id, etransfer_amount, fee_amount, recipient_name,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db
    
    #
    # writes
    #
    async def create(self, customer_id, etransfer_id, amount, fee_amount, recipient_name):
        sql = f"""INSERT INTO etransfers (customer_id, etransfer_id, etransfer_amount, fee_amount,
                                          recipient_name)
                       VALUES ($1, $2, $3, $4, $5)
                    RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, customer_id, etransfer_id, amount, fee_amount, recipient_name)
        return rec


    #
    # reads
    #
    async def get_by_etransfer_id(self, etransfer_id):
        sql = self._base_read() + """ WHERE etransfer_id = $1"""

        rec = await self.db.exec_read(sql, etransfer_id, only_one=True)
        return rec

    
    async def get_by_customer_id(self, customer_id, start_date, end_date):
        sql = self._base_read() + """ WHERE customer_id = $1
                                        AND created_at >= $2
                                        AND created_at <= $3"""

        recs = await self.db.exec_read(sql, customer_id, start_date, end_date)

        return recs
    

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM etransfers"""
        return sql



class EtransferRecipientsRepo(BaseRepo):

    READ_PARAMS = """recipient_id, customer_id, recipient_name, email_address, security_question,
                     security_answer, recipient_status, dc_contact_id,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def create(self, customer_id, rec_name, email, sec_question, sec_answer,
                     status=STATUS_ACTIVE, dc_contact_id=None):
        sql = f"""INSERT INTO etransfer_recipients (customer_id, recipient_name, email_address,
                                                    security_question, security_answer, recipient_status,
                                                    dc_contact_id)
                       VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, customer_id, rec_name, email, sec_question, sec_answer,
                                       status, dc_contact_id)
        
        return rec


    async def change_status(self, recipient_id, status):
        sql = f"""UPDATE etransfer_recipients
                     SET recipient_status = $2
                   WHERE recipient_id = $1
               RETURNING {self.READ_PARAMS}"""

        rec = await self.db.exec_write(sql, recipient_id, status)

        return rec

    
    async def update_contact_id(self, recipient_id, contact_id):
        sql = f"""UPDATE etransfer_recipients
                     SET dc_contact_id = $2
                   WHERE recipient_id = $1
               RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, recipient_id, contact_id)

        return rec

    
    async def update_contact(self, customer_id, recipient_id, rec_name, email, sec_question,
                             sec_answer):
        sql = f"""UPDATE etransfer_recipients
                     SET recipient_name = $3,
                         email_address = $4,
                         security_question = $5,
                         security_answer = $6,
                         updated_at = CURRENT_TIMESTAMP
                   WHERE recipient_id = $2
                     AND customer_id = $1
               RETURNING {self.READ_PARAMS}"""
        
        rec = await self.db.exec_write(sql, customer_id, recipient_id, rec_name, email, sec_question,
                                       sec_answer)
        return rec


    #
    # reads
    #
    async def get_by_recipient_id(self, recipient_id):
        sql = self._base_read() + """ WHERE recipient_id = $1"""

        rec = await self.db.exec_read(sql, recipient_id, only_one=True)
        return rec

    
    async def get_recipient_details(self, customer_id, recipient_id):
        sql = self._base_read() + """ WHERE recipient_id = $1 AND customer_id = $2"""

        rec = await self.db.exec_read(sql, recipient_id, customer_id, only_one=True)

        return rec
    

    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM etransfer_recipients"""
        return sql
