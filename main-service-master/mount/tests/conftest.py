import asyncio
from decimal import Decimal
from unittest.mock import create_autospec
from uuid import UUID, uuid4

import pytest

from app.common import settings
from app.adapters import database


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "datastore: mark test that relies on the data store"
    )


@pytest.yield_fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def pool_connection():
    db = database.PoolConnections(
        read_dsn=settings.READ_DB_DSN,
        write_dsn=settings.WRITE_DB_DSN,
        min_pool_size=1,
        max_pool_size=20,
    )
    await db.connect()
    yield db


@pytest.yield_fixture()
async def db_session(pool_connection):
   session = database.ServiceDB(pool_connection)
   yield session
   await session.close()
