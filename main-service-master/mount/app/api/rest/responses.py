"""Helper methods common to all api entry points"""
import collections
from typing import Any, Dict, List
import dataclasses

import rapidjson
import pydantic

from starlette.responses import Response
from starlette.responses import JSONResponse as StarletteJSONResponse

from app.common import json as json_util
from app.common import errors, logger


def format_field_error(field, code, message):
    return {'field': field, 'code': code, 'message': message}


def format_error(code, message, fields=None):
    err = {
        'code': code,
        'message': message,
    }
    if fields:
        fields = fields if isinstance(fields, list) else [fields]
        err['field_errors'] = fields
    return err


def success(data, meta={}, status_code=200):  # pragma: no cover
    resp = {
        'status': 'success',
        'data': _decode(data),
        'meta': meta
    }
    return _response_from_dict(resp, status_code)


def failure(errors, meta={}, status_code=400):  # pragma: no cover
    errors = errors if isinstance(errors, list) else [errors]
    resp = {
        'status': 'error',
        'errors': _decode(errors),
        'meta': meta
    }
    return _response_from_dict(resp, status_code)


def _decode(data):
    if isinstance(data, list):
        data = [_decode(x) for x in data]

    elif dataclasses.is_dataclass(data):
        data = dataclasses.asdict(data)

    elif isinstance(data, pydantic.BaseModel):
        return data.dict()

    return data


def _response_from_dict(resp, status_code):
    data = _decode(resp)

    json = rapidjson.dumps(
        data,
        datetime_mode=rapidjson.DM_ISO8601 | rapidjson.DM_NAIVE_IS_UTC,
        number_mode=rapidjson.NM_DECIMAL
    )

    return Response(
        json,
        media_type='application/json',
        status_code=status_code,
    )


class JSONResponse(StarletteJSONResponse):
    media_type = "application/json"

    def render(self, content: Any):
        return json_util.stringify(content).encode("utf-8")


class NotAuthorizedResponse(JSONResponse):

    def __init__(self, content: Any):
        err = format_error(errors.E['members_invalid_authorization'], 'Not authorized')
        envelope = {"errors": [err]}

        super().__init__(envelope, status_code=401)

