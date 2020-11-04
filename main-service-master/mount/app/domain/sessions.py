"""Module for handling all the repo functionality for sessions"""
import dataclasses
import uuid

import arrow

from app.common import logger
from app.common import json as json_util
from app.common import security as sek


# Constants
SESSION_PREFIX = 'tipstoday:session:'
SESSION_TTL = 1200  # 20 mins

ENTITY_TYPE_SUPER_ADMIN = 'super-admin'
ENTITY_TYPE_COMPANY_ADMIN = 'company-admin'
ENTITY_TYPE_STORE_ADMIN = 'store-admin'
ENTITY_TYPE_CUSTOMER = 'customer'


def make_session_key(session_id):
    key = f"{SESSION_PREFIX}{session_id}"
    return key


def record_to_dict(rec_obj):
    d = {f:v for (f, v) in rec_obj.items()}
    return d


def gen_session_key():
    return '{}'.format(uuid.uuid4()).replace('-', '')


@dataclasses.dataclass(frozen=True)
class SessionData:
    entity_id: int
    entity_type: str
    session_id: str
    data: dict
    started_at: str = ''
    ttl: int = 0


class SessionsRepo:

    def __init__(self, redis):
        self._redis = redis

    #
    # Writes
    #     
    async def create(self, session_id: str, session_key: str, entity_id: int,
                     entity_type: str, data, started_at=None, ttl=SESSION_TTL):
        started_at = started_at or arrow.utcnow().isoformat()

        data = SessionData(
            entity_id=entity_id,
            entity_type=entity_type,
            data=data,
            started_at=started_at,
            ttl=ttl,
            session_id=session_id,
        )

        jdata = json_util.stringify(dataclasses.asdict(data))
        written = await self._redis.client.setex(session_key, ttl, jdata)
        if not written:
            return False
        
        return data

    
    async def remove(self, session_key: str):
        cleared = await self._redis.client.delete(session_key)        
        return True

    async def extend(self, key, ttl=SESSION_TTL):
        extended = await self._redis.client.expire(key, ttl)
        return True


    #
    # Reads
    #
    async def get(self, session_key):
        jdata = await self._redis.client.get(session_key, encoding='utf-8')

        if not jdata:
            return False
        
        data = json_util.parse(jdata)
        return data

    #
    # Helpers
    #




