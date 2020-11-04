import traceback
from dataclasses import dataclass

import arrow
import requests
import urllib3

from app.common import logger, settings
from app.common import json as json_util

from app.services import dcbank

# to remove warning message
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URI = settings.DC_BANK_BILLPAY_URL
AUTH_TOKEN = settings.DC_BILLPAY_AUTH_TOKEN
CUSTOMER_NUMBER = settings.DC_BILLPAY_CUSTOMER_NUMBER


GET = 'GET'
POST = 'POST'


@dataclass(frozen=True)
class PayeeSearch:
    payee_name: str
    payee_code: str
    
    @staticmethod
    def from_record(rec):
        return PayeeSearch(
            payee_name=rec.get('PayeeName'),
            payee_code=rec.get('PayeeCode'),
        )


def _get_call_uri(endpoint, base_uri=BASE_URI):
    url = f"{base_uri}{endpoint}"
    return url


def _get_base_dict_param():
    base = {
        'CustomerNumber': CUSTOMER_NUMBER,
    }

    return base


async def _do_request(uri, http_method, data, send_json=True, auth_token=AUTH_TOKEN):
    bearer = 'Bearer {}'.format(auth_token)
    headers = {'Content-Type': 'application/json', 'Authorization': bearer}

    res = None
    try:
        if http_method == GET:
            res = requests.get(uri, params=data, headers=headers, verify=False)

        elif http_method == POST:
            if send_json:
                res = requests.post(uri, json=data, headers=headers, verify=False)
            else:
                res = requests.post(uri, data=data, headers=headers, verify=False)

    except Exception as req_exc:
        logger.exception("Request failed: ", uri=uri, method=http_method, data=data,
                         exception=req_exc)
        logger.exception(traceback.format_exc())

    res_data = res.json()
    res_code = True if res_data['IsSucceeded'] else False

    return res_code, res_data 
    

async def search_bill_payees(token):
    endpoint = _get_call_uri('BillPayment/GetPayeeList')

    data = _get_base_dict_param()
    data['Name'] = token

    return await _do_request(endpoint, POST, data)


async def create_bill_payment(payee_name, payee_code, amount, account_number):
    endpoint = _get_call_uri('BillPayment/CreateIndividualBillPayment')

    data = _get_base_dict_param()
    data['PayeeCode'] = payee_code
    data['PayeeName'] = payee_name
    data['PayeeAccountNumber'] = account_number
    data['Amount'] = amount

    return await _do_request(endpoint, POST, data)
