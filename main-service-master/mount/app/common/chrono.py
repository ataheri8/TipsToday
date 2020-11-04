import arrow
import datetime
from dateutil import tz


def format_dates_for_db(thedate):
    try:
        d = arrow.get(thedate).naive
        return d
    except Exception as i:
        raise i
 

def get_current_time_db():
    return arrow.utcnow().naive


def get_last_week_for_db():
    d = arrow.utcnow().floor('hour')
    return d.shift(weeks=-1).naive


def get_last_month_short():
    d = arrow.utcnow().floor('hour')
    return d.shift(months=-1).naive