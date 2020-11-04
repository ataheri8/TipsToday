from app.common import logger, errors
from app.usecases.context import Context

from app.domain import programs

from app.common import security as sek
from app.common import json as json_util


#
# writes
#
async def create(ctx: Context, prog_name, prog_type, subprogram_id, card_type, network,
                 bank, prog_bin, prog_bin_range, processor, printer, printer_client_id,
                 printer_package_id, card_order_type, card_order_freq, pin_enabled=False,
                 pin_change=False):
    pg_repo = programs.ProgramsRepo(ctx.db)

    # not sue what is the best way to check if a program already exists.
    # so, skipping for now
    rec = await pg_repo.create(prog_name, prog_type, subprogram_id, card_type, network, bank,
                               prog_bin, prog_bin_range, processor, printer,
                               printer_client_id, printer_package_id, card_order_type,
                               card_order_freq, pin_enabled=pin_enabled, pin_change=pin_change)

    if rec:
        return True, programs.Program.from_record(rec)
    else:
        return False, errors.E['programs_unable_to_create']


async def disable(ctx: Context, program_id):
    changed = await _change_status(ctx, program_id, programs.STATUS_INACTIVE,
                                   errors.E['programs_unable_to_disable'])
    return changed


async def enable(ctx: Context, program_id):
    changed = await _change_status(ctx, program_id, programs.STATUS_ACTIVE,
                                   errors.E['programs_unable_to_enable'])
    return changed


async def _change_status(ctx: Context, program_id, status, failure_message):
    p_repo = programs.ProgramsRepo(ctx.db)

    exists = await p_repo.get_by_program_id(program_id)

    if not exists:
        return False, errors.E['programs_id_not_found']

    rec = await p_repo.change_status(program_id, status)

    if rec:
        return True, programs.Program.from_record(rec)
    else:
        return False, failure_message



#
# reads
#
async def get_by_program_id(ctx: Context, program_id):
    pg_repo = programs.ProgramsRepo(ctx.db)

    rec = await pg_repo.get_by_program_id(program_id)

    if rec:
        return True, programs.Program.from_record(rec)
    else:
        return False, errors.E['programs_unable_to_view']


async def get_all_programs(ctx: Context, active_only=False, inactive_only=False):
    pg_repo = programs.ProgramsRepo(ctx.db)

    if active_only:
        recs = await pg_repo.search(program_status=programs.STATUS_ACTIVE)
    elif inactive_only:
        recs = await pg_repo.search(program_status=programs.STATUS_INACTIVE)
    else:
        recs = await pg_repo.search()

    progs = [programs.Program.from_record(r) for r in recs]
    return True, progs


