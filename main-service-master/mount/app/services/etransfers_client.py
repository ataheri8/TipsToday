import traceback

import arrow
import requests
import urllib3

from app.common import logger, settings
from app.common import json as json_util

from app.services import dcbank

# to remove warning message
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URI = settings.DC_BANK_ETRANSFER_URL
AUTH_TOKEN = settings.DC_BANK_ETRANSFER_AUTH_TOKEN
CUSTOMER_NUMBER = settings.DC_BANK_ETRANSFER_CUSTOMER_NUMBER


CA_COUNTRY_ID = dcbank.countries_data_en['canada']
ON_PROVINCE_ID = dcbank.canada_provinces_en['ontario']

DEFAULT_CONTACT_TYPE = 'P'

PRIORITY_CODE_RT = 0
PRIORITY_CODE_BULK_REGULAR = 1
PRIORITY_CODE_BULK_PRIORITY = 2

# Transaction Type Codes
MONEY_SEND = 'C'
MONEY_REQUEST = 'D'

GET = 'GET'
POST = 'POST'


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
    

async def send_etransfer(amount, sec_question, sec_answer, contact_id,
                         transaction_type_code=MONEY_SEND, priority_type=PRIORITY_CODE_RT):
    endpoint = _get_call_uri('ETransfer/CreateEtransferTransaction')

    data = _get_base_dict_param()
    data['TransactionTypeCode'] = transaction_type_code
    data['PriorityTypeCode'] = priority_type
    data['Amount'] = amount
    data['ContactId'] = contact_id
    data['DateOfFunds'] = arrow.utcnow().isoformat()
    data['SecurityQuestion'] = sec_question
    data['SecurityQuestionAnswer'] = sec_answer

    return await _do_request(endpoint, POST, data)



async def create_contact(first_name, last_name, email, country_id=CA_COUNTRY_ID, province_id=ON_PROVINCE_ID,
                         contact_type=DEFAULT_CONTACT_TYPE):
    endpoint = _get_call_uri('ETransfer/CreateEtransferContact')

    data = _get_base_dict_param()
    data['ContactTypeCode'] = contact_type
    data['FirstName'] = first_name
    data['LastName'] = last_name
    data['EMail'] = email
    data['CountryId'] = country_id
    data['ProvinceId'] = province_id

    return await _do_request(endpoint, POST, data)


async def update_contact(first_name, last_name, email, contact_id, country_id=CA_COUNTRY_ID,
                         province_id=ON_PROVINCE_ID, contact_type=DEFAULT_CONTACT_TYPE):
    endpoint = _get_call_uri('ETransfer/UpdateEtransferContact')

    data = _get_base_dict_param()
    data['ContactTypeCode'] = contact_type
    data['FirstName'] = first_name
    data['LastName'] = last_name
    data['EMail'] = email
    data['CountryId'] = country_id
    data['ProvinceId'] = province_id
    data['ContactId'] = contact_id
    data['PhoneNumber'] = "1 555-555-5555" # this seems to be required for updating,
                                           # though documentation does not say so

    return await _do_request(endpoint, POST, data)


