from fastapi import APIRouter, Depends, Header, HTTPException
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.common import logger, errors
from app.api.rest.context import RequestContext

from app.usecases import sessions


#
# For now, just wrapping all the auth tags up here
# Can break these out later on if necessary
#
SUPER_ADMIN_AUTH_TOKEN_KEY = 'x-clark-kent'
ADMIN_AUTH_TOKEN_KEY = 'x-barry-allen'
CUSTOMER_AUTH_TOKEN_KEY = 'x-john-stewart'

KEYS = [SUPER_ADMIN_AUTH_TOKEN_KEY, ADMIN_AUTH_TOKEN_KEY, CUSTOMER_AUTH_TOKEN_KEY]


def not_authorized():
    raise HTTPException(status_code=401, detail="Not Authorized")


def not_authorized_type():
    raise HTTPException(status_code=401, detail="Not Authorized Type")


async def _auth(session_id: str, ctx: RequestContext, callback=None,
                extend=True):
    found, sdata = await sessions.view(ctx, session_id)

    if not found or not sdata:
        return callback()

    if extend:
        _, _ = await sessions.extend(ctx, session_id)
    
    return found, sdata


def _parse_auth(request: Request):
    auth_key = [request.headers.get(k) for k in KEYS]
    auth_key = list(filter(None, auth_key))

    if not auth_key:
        # TODO: Normalize this exception
        return None

    session_id = auth_key[0]
    return session_id


async def super_admins(request: Request, ctx: RequestContext = Depends()):
    session_id = _parse_auth(request)

    if not session_id:
        # TODO: Normalize this exception
        return not_authorized()

    found, sdata = await _auth(session_id, ctx, not_authorized)

    if not sdata.get('entity_type') or not sessions.is_super_admin(sdata['entity_type']):
        return not_authorized_type()

    ctx.session = sdata


async def company_admins(request: Request, ctx: RequestContext = Depends()):
    session_id = _parse_auth(request)

    if not session_id:
        # TODO: Normalize this exception
        return not_authorized()

    found, sdata = await _auth(session_id, ctx, not_authorized)

    # super admins can view everything
    if (not sdata.get('entity_type') or
         not (sessions.is_super_admin(sdata['entity_type']) or
              sessions.is_company_admin(sdata['entity_type']))):
        return not_authorized_type()

    ctx.session = sdata


async def store_admins(request: Request, ctx: RequestContext = Depends()):
    session_id = _parse_auth(request)

    if not session_id:
        # TODO: Normalize this exception
        return not_authorized()

    found, sdata = await _auth(session_id, ctx, not_authorized)

    # super admins can view everything
    if (not sdata.get('entity_type') or
         not (sessions.is_super_admin(sdata['entity_type']) or
              sessions.is_store_admin(sdata['entity_type']))):
        return not_authorized_type()

    ctx.session = sdata


# for either store or company admins
async def admins(request: Request, ctx: RequestContext = Depends()):
    session_id = _parse_auth(request)

    if not session_id:
        # TODO: Normalize this exception
        return not_authorized()

    found, sdata = await _auth(session_id, ctx, not_authorized)

    # super admins can view everything
    if (not sdata.get('entity_type') or
         not (sessions.is_super_admin(sdata['entity_type']) or
              sessions.is_company_admin(sdata['entity_type']) or
              sessions.is_store_admin(sdata['entity_type']))):
        return not_authorized_type()

    ctx.session = sdata


async def customers(request: Request, ctx: RequestContext = Depends()):
    session_id = _parse_auth(request)

    if not session_id:
        # TODO: Normalize this exception
        return not_authorized()

    found, sdata = await _auth(session_id, ctx, not_authorized)

    # super admins can view everything
    if (not sdata.get('entity_type') or
        not (sessions.is_super_admin(sdata['entity_type']) or
             sessions.is_customer(sdata['entity_type']))):
        return not_authorized_type()

    ctx.session = sdata
