"""init/boot file for api"""
import datadog

from app.common import settings, logger
from app.api.rest import bootstrap

datadog_options = {
    'statsd_host': settings.STATSD_HOST,
    'statsd_port': settings.STATSD_PORT
}
datadog.initialize(**datadog_options)

restapi = bootstrap()
logger.info('rest api is ready')

