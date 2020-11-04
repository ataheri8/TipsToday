'''Module for working with db connections'''
# -*- coding: utf-8 -*-
import asyncio
import traceback

from contextlib import contextmanager
from dataclasses import dataclass

import asyncpg
from asyncpg import create_pool

from app.common.asyncio import run_async
from app.common import logger, settings
from app.domain import DBQueryExecutor


#       
# Database classes
#
class DBError(Exception):
    pass


class DBConnectionError(DBError):
    pass


class DBExecutionError(DBError):
    pass


class PoolConnections:
    
    def __init__(self, write_dsn, read_dsn, min_pool_size, max_pool_size):
        self.write_dsn = write_dsn
        self.read_dsn = read_dsn
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size
        self._write_pool = None
        self._read_pool = None

    async def connect(self):
        if self._read_pool and self._write_pool:
            return
        
        logger.info("init db connection pools")
        self._read_pool = await create_pool(self.read_dsn,
                                            min_size=self.min_pool_size,
                                            max_size=self.max_pool_size)
        self._write_pool = await create_pool(self.write_dsn,
                                             min_size=self.min_pool_size,
                                             max_size=self.max_pool_size)

    @property
    def read_pool(self):
        if not self._read_pool:
            raise DBConnectionError("Read pool - not connected")
        return self._read_pool

    @property
    def write_pool(self):
        if not self._write_pool:
            raise DBConnectionError("Write pool - not connected")
        return self._write_pool

    async def close(self):
        logger.exception("Closing pool connections")
        try:
            await self._read_pool.close()
            await self._write_pool.close()
        except Exception as err:
            logger.exception("Unable to close pool connections", err=err)
            logger.exception(traceback.format_exc())



class ServiceDB(DBQueryExecutor):
    
    def __init__(self, pool_conn: PoolConnections):
        self._pool_conn = pool_conn
        self._write_conn = None
        self._read_conn = None

    async def _write_connection(self):
        if not self._write_conn:
            self._write_conn = await self._pool_conn.write_pool.acquire()
        return self._write_conn

    async def _read_connection(self):
        if not self._read_conn:
            self._read_conn = await self._pool_conn.read_pool.acquire()
        return self._read_conn

    async def close(self):
        if self._read_conn:
            await self._pool_conn.read_pool.release(self._read_conn)
        
        if self._write_conn:
            await self._pool_conn.write_pool.release(self._write_conn)

    async def exec_write(self, query, *params, auto_commit=True):
        try:
            conn = await self._write_connection()
            rec = await conn.fetchrow(query, *params)
            return rec

        except Exception as err:
            logger.exception("Db write error! ", query=query, params=params)
            logger.exception(traceback.format_exc())
            raise DBExecutionError() from err

    async def exec_write_many(self, query, params, auto_commit=False):
        try:
            conn = await self._write_connection()
            rec = await conn.executemany(query, params)
            return rec

        except Exception as err:
            logger.exception("Db write many error! ", query=query, params=params)
            logger.exception(traceback.format_exc())
            raise DBExecutionError() from err

    async def exec_read(self, query, *params, only_one=False):
        logger.debug("Executing DB Read", query=query, params=params,
                     only_one=only_one)
        try:
            conn = await self._read_connection()
            if only_one:
                result = await conn.fetchrow(query, *params)
            else:
                result = await conn.fetch(query, *params)

        except Exception as err:
            logger.exception("db read error: ", query=query, params=params,
                             only_one=only_one)
            logger.exception(traceback.format_exc())
            raise DBExecutionError() from err

        else:
            logger.debug("executing db read: ", query=query, params=params,
                         only_one=only_one, result=result)
            return result

