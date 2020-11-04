import decimal
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel

from app.common import logger, errors
from app.api.rest import responses, authorizations

from app.api.rest.context import RequestContext

from app.usecases import programs


router = APIRouter()


#
# Inputs
#
class NewProgramIn(BaseModel):
    program_name: str
    program_type: str
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
    subprogram_id: str
    pin_enabled: int = 0
    pin_change: int = 0


#
# Outputs
#
class ProgramOut(BaseModel):
    program_id: int
    program_name: str
    program_type: str
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
    pin_enabled: int
    pin_change: int

    @staticmethod
    def from_program(d):
        return ProgramOut(
            program_id=d.program_id,
            program_name=d.program_name,
            program_type=d.program_type,
            subprogram_id=d.subprogram_id,
            card_type=d.card_type,
            network=d.network,
            sponsoring_bank=d.sponsoring_bank,
            program_bin=d.program_bin,
            program_bin_range=d.program_bin_range,
            processor=d.processor,
            printer=d.printer,
            printer_client_id=d.printer_client_id,
            printer_package_id=d.printer_package_id,
            card_order_type=d.card_order_type,
            card_order_frequency=d.card_order_frequency,
            created_at=d.created_at,
            updated_at=d.updated_at,
            pin_enabled=d.pin_enabled,
            pin_change=d.pin_change,
        )


@router.post("/programs", response_model=ProgramOut,
             dependencies=[Depends(authorizations.super_admins)])
async def create_program(args: NewProgramIn, ctx: RequestContext = Depends()):
    made, data = await programs.create(ctx,
                                       args.program_name,
                                       args.program_type,
                                       args.subprogram_id,
                                       args.card_type,
                                       args.network,
                                       args.sponsoring_bank,
                                       args.program_bin,
                                       args.program_bin_range,
                                       args.processor,
                                       args.printer,
                                       args.printer_client_id,
                                       args.printer_package_id,
                                       args.card_order_type,
                                       args.card_order_frequency)
    if made:
        resp = ProgramOut.from_program(data)
        return responses.success(resp, status_code=201)
    else:
        err = responses.format_error(data, "Unable to create")
        return responses.failure(err)


@router.get("/programs/{program_id}", response_model=ProgramOut,
            dependencies=[Depends(authorizations.super_admins)])
async def view_program_details(program_id: int, ctx: RequestContext = Depends()):
    res, data = await programs.get_by_program_id(ctx, program_id)

    if res:
        resp = ProgramOut.from_program(data)
        return responses.success(resp)
    else:
        err = responses.format_error(data, "unable to view")
        return responses.failure(err)


@router.delete("/programs/{program_id}", response_model=ProgramOut,
               dependencies=[Depends(authorizations.super_admins)])
async def disable_program(program_id: int, ctx: RequestContext = Depends()):
    res, data = await programs.disable(ctx, program_id)

    if res:
        resp = ProgramOut.from_program(data)
        return responses.success(resp)
    else:
        err = responses.format_error(data, "unable to update")
        return responses.failure(err)


@router.get("/programs", response_model=List[ProgramOut],
            dependencies=[Depends(authorizations.super_admins)])
async def view_programs(ctx: RequestContext = Depends()):
    res, data = await programs.get_all_programs(ctx)

    resp = [ProgramOut.from_program(d) for d in data]
    return responses.success(resp)

