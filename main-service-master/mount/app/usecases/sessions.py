import uuid

from app.common import logger, errors
from app.usecases.context import Context

from app.domain import sessions


# Writes
async def extend(ctx: Context, session_id: str):
    srepo = sessions.SessionsRepo(ctx.redis)
    ses_key = sessions.make_session_key(session_id)

    data = await srepo.get(ses_key)

    if not data:
        return False, errors.E['sessions_invalid_session']

    sdata = await srepo.extend(ses_key)

    return True, sdata


async def remove(ctx: Context, session_id: str):
    srepo = sessions.SessionsRepo(ctx.redis)
    ses_key = sessions.make_session_key(session_id)
    data = await srepo.get(ses_key)

    if not data:
        return False, errors.E['sessions_invalid_session']

    deleted = await srepo.remove(session_id)
    if not deleted:
        return False, errors.E['sessions_unable_to_clear_session']

    return True, deleted


# Reads
async def view(ctx: Context, session_id: str):
    srepo = sessions.SessionsRepo(ctx.redis)
    ses_key = sessions.make_session_key(session_id)

    data = await srepo.get(ses_key)

    if not data:
        return False, errors.E['sessions_invalid_session']
    logger.warning("session_view data is --> ", d=data)
    return True, data


#
# Helpers
#
def is_super_admin(entity_type):
    return _check(entity_type, sessions.ENTITY_TYPE_SUPER_ADMIN)


def is_company_admin(entity_type):
    return _check(entity_type, sessions.ENTITY_TYPE_COMPANY_ADMIN)


def is_store_admin(entity_type):
    return _check(entity_type, sessions.ENTITY_TYPE_STORE_ADMIN)


def is_customer(entity_type):
    return entity_type.strip().lower() == sessions.ENTITY_TYPE_CUSTOMER
    

def _check(entity_type, required_type):
    return entity_type.strip().lower() == required_type