from fastapi import APIRouter

from . import clients
from . import super_admins
from . import admins
from . import customers
from . import stores
from . import fees
from . import programs


router = APIRouter()
router.include_router(super_admins.router)
router.include_router(programs.router)
router.include_router(clients.router)
router.include_router(admins.router)
router.include_router(customers.router)
router.include_router(stores.router)
router.include_router(fees.router)


