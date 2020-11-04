"""init file for restul api"""
from fastapi import FastAPI

from starlette.staticfiles import StaticFiles

from app.adapters import database, redis
from app.common import logger, settings
from app.common.metrics import Metrics

from app.api.rest import middlewares


def init_services(app):

    @app.on_event("startup")
    async def init_db_conn_pool():
        app.db_conns = database.PoolConnections(
            write_dsn=settings.WRITE_DB_DSN,
            read_dsn=settings.READ_DB_DSN,
            min_pool_size=settings.DB_MIN_POOL_SIZE,
            max_pool_size=settings.DB_MAX_POOL_SIZE
        )
        await app.db_conns.connect()

    @app.on_event("startup")
    async def init_redis_conn_pool():
        app.redis_conns = redis.RedisPoolConnections(
            settings.REDIS_HOST,
            settings.REDIS_PORT,
            min_pool_size=settings.REDIS_MIN_POOL_SIZE,
            max_pool_size=settings.REDIS_MAX_POOL_SIZE
        )
        await app.redis_conns.connect()
    
    @app.on_event("shutdown")
    async def close_db_conn_pool():
        await app.db_conns.close()

    
    @app.on_event("shutdown")
    async def close_redis_conn_pool():
        await app.redis_conns.close()
        await app.redis_conns.wait_closed()
    

def init_middleware(app):
    app.add_middleware(middlewares.DBSessionMiddleware)
    app.add_middleware(middlewares.RedisSessionMiddleware)
    app.add_middleware(middlewares.RestContextMiddleware)
    app.add_middleware(middlewares.LogRequestMiddleWare)
    app.add_middleware(middlewares.MetricsMiddleware,
                        metrics=Metrics('restapi', settings.APP_ENV))


def init_routes(app):
    if settings.APP_ENV == 'local' or settings.UNIT_TEST:
        logger.info('Serving test coverage reports at /tests')
        app.mount('/tests', app=StaticFiles(
            directory='/srv/root/tests/htmlcov/',
            html=True,
            check_dir=False
        ))

    from . import v1
    app.include_router(v1.router, prefix="/v1")

    from . import monitoring
    app.include_router(monitoring.router)


def bootstrap():
    logger.warning("rest api starting")
    api = FastAPI(
        title="Tipstoday API",
        description="",
        docs_url=None,
        redoc_url="/docs"
    )

    init_services(api)
    init_middleware(api)
    init_routes(api)

    return api




