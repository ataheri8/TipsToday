"""
This document will test all the parameters in an FIS call to
ensure the data is valid. It will not be testing the FIS side
validity, only if the data being passed is in the correct
format
"""

#from FIS_Calls import *
import re
import asyncio
from cerberus import Validator
from datetime import datetime

to_date = lambda s: datetime.strptime(s, '%Y-%m-%d')


def address_check(field, value, error):
    if re.search('^[0-9]+( [A-Z]+)+$', str(value).upper()) is None:
        error(field, "Must be comprised of a street number with a street name")


def zipcode_check(field, value, error):
    if re.search('^[A-Z][1-9][A-Z] [1-9][A-Z][1-9]$', str(value).upper()) is None:
        error(field, "Postal code must be comprised in the format of {LNL NLN}")


schema = {'firstname:': {'type': 'string'},
          'lastname:': {'type': 'string'},
          'middlename': {'type': 'string', 'nullable': True},
          'personid': {'type': 'string', 'minlength': 10, 'maxlength': 10},
          'amount': {'type': 'float'},
          'ssn': {'type': 'integer', 'maxlength': 9, 'minlength': 9},
          'address': {'type': 'string', 'check_with': address_check},
          'city': {'type': 'string'},
          'state': {'type': 'string', 'maxlength': 2, 'minlength': 2},
          'zipcode': {'type': 'string', 'check_with': zipcode_check},
          'country': {'type': 'string', 'allowed': ['840', '006']},
          'proxykey': {'type': 'string', 'nullable': True},
          'proxykey2': {'type': 'string'},
          'loadamount': {'type': 'float'},
          'latitude': {'type': 'float', 'min': 0, 'max': 180},
          'longitude': {'type': 'float', 'min': 0, 'max': 180},
          'StartDate': {'type': 'datetime', 'coerce': to_date, 'nullable':True},
          'Days': {'type': 'integer', 'min': 0, 'max': 30, 'nullable':True},
          'status': {'type': 'string', 'allowed': ['ACTIVATE', 'CLOSE', 'SUSPEND', 'UNSUSPEND',
                                                   'LOSTSTOLEN', 'MARK_PFRAUD', 'UNMARK_PFRAUD', 'MARK_FRAUD']},
          'newpin': {
              'anyof': [
                  {
                      'type': 'integer',
                      'maxlength': 4,
                      'minlength': 4
                  },
                  {
                      'type': 'string',
                      'allowed': ['RANDOM']
                  }
              ]
              }
          }

v = Validator(schema, allow_unknown=True)


async def create_fis_user_check(userid, pwd, sourceid, clientid, subprogid, pkgid, first, last,
                                ssn, addr1, city, state, zipcode, country, mi=None, proxykey=None):

    data = {'userid': userid, 'pwd': pwd, 'sourceid': sourceid, 'clientid': clientid, 'subprogid': subprogid,
            'pkgid': pkgid, 'first': first, "last": last, "ssn": ssn, "addr1": addr1,
            "city": city, "state": state, "zipcode": zipcode, "country": country, "mi": mi,
            "proxykey": proxykey}

    return v.validate(data, schema), v.errors, data


async def activate_card_check(personid, proxykey):

    data = {'personid': personid, 'proxykey': proxykey}

    return v.validate(data, schema), v.errors

async def get_transactions_check(proxykey, StartDate, Days):

    data = {'proxykey': proxykey, 'StartDate': StartDate, "Days": Days}

    return v.validate(data, schema), v.errors


async def check_balance_check(proxykey):

    data = {'proxykey': proxykey}

    return v.validate(data, schema), v.errors


async def create_person_check(first: str, last: str, addr1, city, country, ssn, mi=None):

    data = {"first": first, "last": last, "addr1": addr1, "city": city, "country": country,
            "ssn": ssn, "mi": mi}

    return v.validate(data, schema), v.errors


async def update_person_check(first: str, last: str, personid):

    data = {"firstname": first, "lastname": last, "personid": personid}

    return v.validate(data, schema), v.errors


async def load_value_check(proxykey, loadamount):

    data = {'proxykey': proxykey, 'loadamount': loadamount}

    return v.validate(data, schema), v.errors


async def get_acct_status_check(proxykey):

    data = {'proxykey': proxykey}

    return v.validate(data, schema), v.errors


async def change_status_check(status, proxykey):

    data = {'status': status, 'proxykey': proxykey}

    return v.validate(data, schema), v.errors


async def change_pin_check(proxykey, newpin):

    data = {'proxykey': proxykey, 'newpin': newpin}

    return v.validate(data, schema), v.errors


async def card_to_card_transfer_check(sender_proxy, receiver_proxy, amount):

    data = {'proxykey': sender_proxy, 'proxykey2': receiver_proxy, 'loadamount': amount}

    return v.validate(data, schema), v.errors


async def get_atm_locations_check(latitude, longitude):

    data = {'latitude': latitude, 'longitude': longitude}

    return v.validate(data, schema), v.errors