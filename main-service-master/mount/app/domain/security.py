"""Module for handling all the repo functionality for customer security"""
import dataclasses
import uuid
import random

import arrow

from app.common import logger
from app.common import json as json_util
from app.common import security as sek


# Constants
KEY_PREFIX = 'tipstoday:security:reset:'
RESET_TTL = 3600  # 1 hour


def make_key(value):
    _val = f"{value}".lower().strip()
    key = f"{KEY_PREFIX}{_val}"
    return key


def generate_token():
    return random.randint(100000, 999999)


class SecurityRepo:

    def __init__(self, redis):
        self._redis = redis

    #
    # Writes
    #
    async def store_token(self, key, identifier, entity_id, ttl=RESET_TTL):
        data = json_util.stringify(
            {'identifier': identifier, 'entity_id': entity_id}
        )
        written = await self._redis.client.setex(key, ttl, data)

        if not written:
            return False
        
        return written


    #
    # Reads
    #
    async def get_token(self, key):
        jdata = await self._redis.client.get(key, encoding='utf-8')
        if not jdata:
            return False

        data = json_util.parse(jdata)
        return data


    #
    # Helpers
    #




