import sys
import logging
from _contextvars import ContextVar
from uuid import uuid4

import structlog

from app.common import settings

# Custom Processors
_request_id_context = ContextVar("request_id")


# Log setup
IS_CONFIGURED = False


def _log_as_txt():
    return settings.APP_ENV == "local" or settings.UNIT_TEST


def _setup():
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    _configure_std_logging(shared_processors)
    _configure_internal_logging(shared_processors)


def _configure_std_logging(shared_processors):
    if _log_as_txt():
        renderer = structlog.dev.ConsoleRenderer(colors=False)
    else:
        renderer = structlog.processors.JSONRenderer()

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer, foreign_pre_chain=shared_processors
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(settings.API_LOG_LEVEL)
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.API_LOG_LEVEL)


def _configure_internal_logging(shared_processors):
    procs = [
        # _add_request_id_processor,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]
    structlog.configure(
        processors=shared_processors + procs,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def set_request_id(request_id=None):
    r_id = request_id if request_id else str(uuid4())
    _request_id_context.set(r_id)


# Logger operations
def get_logger():
    global IS_CONFIGURED  # pylint: disable=global-statement
    if not IS_CONFIGURED:
        _setup()
        IS_CONFIGURED = True

    return structlog.wrap_logger(logging.getLogger())


def debug(*args, **kwargs):
    return get_logger().debug(*args, **kwargs)


def info(*args, **kwargs):
    return get_logger().info(*args, **kwargs)


def warning(*args, **kwargs):
    return get_logger().warning(*args, **kwargs)


def critical(*args, **kwargs):
    return get_logger().critical(*args, **kwargs)


def exception(*args, **kwargs):
    return get_logger().exception(*args, **kwargs)


def error(*args, **kwargs):
    return get_logger().error(*args, **kwargs)
