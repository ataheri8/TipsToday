"""Module for handling all the repo functionality for stores"""
from dataclasses import dataclass, field
from typing import List

from app.common import logger
from app.common import json as json_util
from app.common import security as sek

from app.domain import DBQueryExecutor, BaseRepo


@dataclass(frozen=True)
class Program:
    program_id: int
    program_name: str
    program_type: str
    program_status: str
    subprogram_id: str
    card_type: str
    network: str
    sponsoring_bank: str
    program_bin: str
    program_bin_range: str
    processor: str
    printer: str
    printer_client_id: str
    printer_package_id: str
    card_order_type: str
    card_order_frequency: str
    created_at: str
    updated_at: str
    pin_enabled: int = 0
    pin_change: int = 0

    @staticmethod
    def from_record(rec):
        return Program(
            program_id=rec.get('program_id'),
            program_name=rec.get('program_name'),
            program_type=rec.get('program_type'),
            program_status=rec.get('program_status'),
            subprogram_id=rec.get('subprogram_id'),
            card_type=rec.get('card_type'),
            network=rec.get('network'),
            sponsoring_bank=rec.get('sponsoring_bank'),
            program_bin=rec.get('program_bin'),
            program_bin_range=rec.get('program_bin_range'),
            processor=rec.get('processor'),
            printer=rec.get('printer'),
            printer_client_id=rec.get('printer_client_id'),
            printer_package_id=rec.get('printer_package_id'),
            card_order_type=rec.get('card_order_type'),
            card_order_frequency=rec.get('card_order_frequency'),
            created_at=rec.get('created_at'),
            updated_at=rec.get('updated_at'),
            pin_enabled=rec.get('pin_enabled'),
            pin_change=rec.get('pin_change'),
        )


STATUS_ACTIVE = 'active'
STATUS_INACTIVE = 'inactive'


class ProgramsRepo(BaseRepo):

    READ_PARAMS = """program_id, program_name, program_type, program_status, subprogram_id,
                     card_type, network, sponsoring_bank, program_bin,
                     program_bin_range, processor, printer, printer_client_id,
                     printer_package_id, card_order_type, card_order_frequency,
                     pin_enabled, pin_change,
                     EXTRACT(EPOCH FROM updated_at) as updated_at,
                     EXTRACT(EPOCH FROM created_at) as created_at"""

    def __init__(self, db: DBQueryExecutor):
        self.db = db

    #
    # writes
    #
    async def create(self, prog_name, prog_type, subprogram_id, card_type, network, sponsor_bank,
                     prog_bin, prog_bin_range, processor, printer, printer_client_id,
                     printer_package_id, card_order_type, card_order_frequency,
                     prog_status=STATUS_ACTIVE, pin_enabled=0, pin_change=0):
        sql = f"""INSERT INTO programs (program_name, program_type, program_status, subprogram_id,
                                        card_type, network, sponsoring_bank,
                                        program_bin, program_bin_range, processor,
                                        printer, printer_client_id, printer_package_id,
                                        card_order_type, card_order_frequency,
                                        pin_enabled, pin_change)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11,
                               $12, $13, $14, $15, $16, $17)
                    RETURNING {self.READ_PARAMS}"""

        rec = await self.db.exec_write(sql, prog_name, prog_type, prog_status, subprogram_id,
                                       card_type, network, sponsor_bank, prog_bin,
                                       prog_bin_range, processor, printer,
                                       printer_client_id, printer_package_id,
                                       card_order_type, card_order_frequency,
                                       pin_enabled, pin_change)
        return rec


    async def change_status(self, program_id, status):
        sql = f"""UPDATE programs
                     SET program_status = $2
                   WHERE program_id = $1
               RETURNING {self.READ_PARAMS}"""

        rec = await self.db.exec_write(sql, program_id, status)
        return rec


    #
    # reads
    #
    async def get_by_program_id(self, program_id):
        sql = self._base_read() + """ WHERE program_id = $1"""

        rec = await self.db.exec_read(sql, program_id, only_one=True)
        return rec


    #
    # utils
    #
    def _base_read(self):
        sql = f"""SELECT {self.READ_PARAMS}
                   FROM programs"""
        return sql
