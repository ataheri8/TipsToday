'''Module for working with redis connections'''
# -*- coding: utf-8 -*-
import asyncio
import traceback

from contextlib import contextmanager
from dataclasses import dataclass

import aioredis

from app.common.asyncio import run_async
from app.common import logger, settings


class RedisError(Exception):
    pass


class RedisConnectionError(RedisError):
    pass


class RedisPoolConnections:

    def __init__(self, host, port, min_pool_size=1, max_pool_size=10):
        self.host = host
        self.port = port
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self._pool_dsn = f"redis://{self.host}:{self.port}"
        self._pool = None
    
    async def connect(self):
        if self._pool:
            return

        logger.info("init redis connection pool")
        self._pool = await aioredis.create_redis_pool(self._pool_dsn,
                                                      minsize=self.min_pool_size,
                                                      maxsize=self.max_pool_size)

    @property
    def pool_conn(self):
        if not self._pool:
            raise RedisConnectionError("Redis pool - not connected")
        return self._pool

    async def close(self):
        logger.exception("Closing redis pool connections")
        try:
            self._pool.close()
            await self._pool.wait_closed()
        
        except Exception as err:
            logger.exception("Unable to close redis pool connections", err=err)
            logger.exception(traceback.format_exc())


class ServiceRedis:

    def __init__(self, pool_conn):
        self._pool = pool_conn
        self._conn = None

    @property
    def client(self):
        if not self._conn:
            self._conn = self._pool.pool_conn
        return self._conn

    async def close(self):
        if self._pool:
            await self._pool.pool_conn.release()
