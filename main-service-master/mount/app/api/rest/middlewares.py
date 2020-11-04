import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match

from app.adapters import database, redis
from app.common import logger
from app.common.metrics import Metrics

from app.api.rest import context


class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        db = database.ServiceDB(request.app.db_conns)
        request.state.db = db

        try:
            return await call_next(request)
        finally:
            await db.close()


class RedisSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        r = redis.ServiceRedis(request.app.redis_conns)
        request.state.redis = r
        request.state.session = {}
        try:
            return await call_next(request)
        finally:
            # await r.close()
            pass


class LogRequestMiddleWare(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        resp = await call_next(request)

        logger.info(
            'rest requests log --',
            user_agent=request.headers['user-agent'],
            method=request.method,
            url=request.url.path,
            client=f'{request.client.host}:{request.client.port}',
            status_code=resp.status_code,
        )

        return resp


class RestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.context = context.RequestContext(request)

        return await call_next(request)


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, metrics: Metrics, **kwargs):
        self.metrics = metrics        
        super().__init__(app, **kwargs)

    @staticmethod
    def find_route(router, scope):
        for route in router.routes:
            match, _ = route.matches(scope)
            if match != Match.NONE:
                return route.path
        else:
            return scope['path']

    async def dispatch(self, request, call_next):
        route = MetricsMiddleware.find_route(request.app.router, request.scope)
        request_start_time = time.time()
        logger.set_request_id(request.headers.get('x-request-id'))

        response = await call_next(request)

        self.metrics.count_requests(route)
        total_seconds = time.time() - request_start_time
        self.metrics.request_latency(route, total_seconds)
        
        response.headers['X-Process-Time'] = str(total_seconds)
        return response
