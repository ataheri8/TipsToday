from starlette.requests import Request

from app.usecases.context import Context
from app.common import logger


class RequestContext(Context):
    def __init__(self, request: Request):
        self._request = request

    @property
    def db(self):
        return self._request.state.db

    @property
    def redis(self):
        return self._request.state.redis

    @property
    def session(self):
        return self._request.state.session

    @session.setter
    def session(self, d):
        self._request.state.session = d

    def __str__(self):
        return str(
            {
                "db": self.db,
                "redis": self.redis,
            }
        )

