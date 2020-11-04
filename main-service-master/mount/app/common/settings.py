import socket

from starlette.config import Config

config = Config()

HOSTNAME = config('HOSTNAME', default=socket.gethostname())
APP_ENV = config('APP_ENV', default='local')
UNIT_TEST = config('UNIT_TEST', cast=bool, default=False)

DB_NAME = config('DB_NAME', default='')
READ_DB_USER = config('READ_DB_USER', default='postgres')
READ_DB_PASS = config('READ_DB_PASS', default='example')
READ_DB_HOST = config('READ_DB_HOST', default='localhost')
READ_DB_PORT = config('READ_DB_PORT', cast=int, default=5432)
WRITE_DB_USER = config('WRITE_DB_USER', default='postgres')
WRITE_DB_PASS = config('WRITE_DB_PASS', default='example')
WRITE_DB_HOST = config('WRITE_DB_HOST', default='localhost')
WRITE_DB_PORT = config('WRITE_DB_PORT', cast=int, default=5432)

DB_MIN_POOL_SIZE = config("DB_MIN_POOL_SIZE", cast=int, default=1)
DB_MAX_POOL_SIZE = config("DB_MAX_POOL_SIZE", cast=int, default=2)

READ_DB_DSN = 'postgresql://{}:{}@{}:{}/{}?sslmode=prefer'.format(READ_DB_USER,
                                                                READ_DB_PASS,
                                                                READ_DB_HOST,
                                                                READ_DB_PORT,
                                                                DB_NAME)
WRITE_DB_DSN = 'postgresql://{}:{}@{}:{}/{}?sslmode=prefer'.format(WRITE_DB_USER,
                                                                 WRITE_DB_PASS,
                                                                 WRITE_DB_HOST,
                                                                 WRITE_DB_PORT,
                                                                 DB_NAME)
REDIS_HOST = config('REDIS_HOST', default='redis')
REDIS_PORT = config('REDIS_PORT', cast=int, default=6379)
REDIS_MIN_POOL_SIZE = config('REDIS_MIN_POOL_SIZE', cast=int, default=3)
REDIS_MAX_POOL_SIZE = config('REDIS_MAX_POOL_SIZE', cast=int, default=10)


API_LOG_LEVEL = config('API_LOG_LEVEL', cast=int, default=10)

STATSD_HOST = config('STATSD_HOST', default='statsd.monitoring')
STATSD_PORT = config('STATSD_PORT', default='8125')

TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID')
TWILIO_ACCOUNT_TOKEN = config('TWILIO_ACCOUNT_TOKEN')
TWILIO_FROM_NUMEBR = config('TWILIO_FROM_NUMBER')

FIS_CARD_TYPE = config('FIS_CARD_TYPE')
FIS_PACKAGE_ID = config('FIS_PACKAGE_ID')
FIS_URL = config('FIS_URL')
FIS_SUB_PROGRAM_ID = config('FIS_SUB_PROGRAM_ID')
FIS_PWD = config('FIS_PWD')
FIS_CERT_PATH = config('FIS_CERT_PATH')
FIS_CERT_PWD = config('FIS_CERT_PWD')
FIS_SOURCE_ID = config('FIS_SOURCE_ID')
FIS_CLIENT_ID = config('FIS_CLIENT_ID')
FIS_USER_ID = config('FIS_USER_ID')

DC_BANK_ETRANSFER_URL = config('DC_BANK_URL')
DC_BANK_BILLPAY_URL = config('DC_BANK_URL')
DC_BANK_ETRANSFER_CUSTOMER_NUMBER = config('DC_ETRANSFER_CUSTOMER_NUMBER')
DC_BANK_ETRANSFER_AUTH_TOKEN = config('DC_ETRANSFER_AUTH_TOKEN')
DC_BILLPAY_CUSTOMER_NUMBER = config('DC_BILLPAY_CUSTOMER_NUMBER')
DC_BILLPAY_AUTH_TOKEN = config('DC_BILLPAY_AUTH_TOKEN')

