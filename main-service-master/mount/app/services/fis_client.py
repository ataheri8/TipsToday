import xmltodict
import re
import uuid

import requests_pkcs12 as pkcs12
import arrow

from app.common import logger, settings
from app.common import json as json_util


CERT_FILE = settings.FIS_CERT_PATH
CERT_PWD = settings.FIS_CERT_PWD

BASE_URI = settings.FIS_URL

DEFAULT_GOVT_ID = '999999999'
CA_COUNTRY_ID = '006'
US_COUNTRY_ID = '840'


def _get_call_uri(endpoint, base_uri=BASE_URI):
    url = f"{base_uri}{endpoint}"
    return url


def _get_base_dict_param():
    base = {
        'userid': settings.FIS_USER_ID,
        'pwd': settings.FIS_PWD,
        'sourceid': settings.FIS_SOURCE_ID,
        'clientid': settings.FIS_CLIENT_ID,
        'subprogid': settings.FIS_SUB_PROGRAM_ID,
        'pkgid': settings.FIS_PACKAGE_ID,
    }

    return base


def parse_pipe_response(data):
    return data.split('|')


def xml_to_dict(xml: str):
    new_dict = dict()
    split = xml.split("</Schema>")
    rows = split[1].replace("#", "").replace("Tran Date", "TranDate")\
                   .replace("Post Date", "PostDate").replace("</XML>", "")\
                   .replace("r:ROW", "Transactions").replace("@", "")

    new_dict = dict(xmltodict.parse(rows))["r:ROOT"]

    final_dict = json_util.parse(re.sub('@', '', json_util.stringify(new_dict)))

    if final_dict['Response'] == "1":
        return final_dict
    else:
        return final_dict


async def _do_request(uri, data, cert_file=CERT_FILE, cert_pwd=CERT_PWD,
                     allow_redirects=False):
    pattern_succ = "^1 .*"
    prog = re.compile(pattern_succ)

    req = pkcs12.post(uri, 
                      data=data,
                      pkcs12_filename=cert_file,
                      pkcs12_password=cert_pwd,
                      allow_redirects=allow_redirects)

    logger.warning("REQUEST BODY -->", req_body=req.request.body)
    logger.warning("REQUEST HEADERS -->", req_head=req.request.headers)

    res_check = prog.match(req.text)
    if res_check is not None:
        # we have great success
        split = req.text.split(' ')
        result = split[1].replace('^', '')
        return True, result

    else:
        # we have great failure
        return False, req.text


async def activate_card(proxy, first_name, last_name, city,
                        country='ca',
                        govt_id=DEFAULT_GOVT_ID):
    _country = country.lower()
    endpoint = _get_call_uri("CO_AssignCard.asp")
    data = _get_base_dict_param()
    data['proxykey'] = proxy
    data['first'] = first_name
    data['last'] = last_name
    data['city'] = city
    data['country'] = CA_COUNTRY_ID if _country == 'ca' else US_COUNTRY_ID
    data['ssn'] = govt_id

    res, res_data = await _do_request(endpoint, data)
    return res, res_data


async def get_proxy_status(proxy):
    endpoint = _get_call_uri("CO_GetAcctStatus.asp")
    data = _get_base_dict_param()
    data['proxykey'] = proxy

    res, res_data = await _do_request(endpoint, data)
    logger.warning("#### get_proxy_status --> ", res=res, res_data=res_data)
    return res, res_data


async def get_proxy_balance(proxy):
    endpoint = _get_call_uri("CO_OTB_ByProxy.asp")
    data = _get_base_dict_param()
    data['proxykey'] = proxy

    res, res_data = await _do_request(endpoint, data)
    logger.warning("#### Get proxy balance --> ", res=res, res_data=res_data)
    return res, res_data


async def get_proxy_transactions(proxy, from_date=None, days=31):
    endpoint = _get_call_uri("CO_GetCardTxns.asp")
    data = _get_base_dict_param()
    data['ProxyKey'] = proxy
    # data['CardnumOnly'] = 0
    # data['resp'] = "xml"
    # data['Days'] = days
    data['StartDate'] = arrow.utcnow().format('YYYY-MM-DD')

    if from_date:
        data['StartDate'] = from_date
    

    res, res_data = await _do_request(endpoint, data)
    logger.warning("GET_PROXY_TRANSACTIONS ---> ", res=res, res_data=res_data)
    # _res_data = xml_to_dict(res_data)
    # logger.warning("GET_PROXY_TRANSACTIONS ---> ", res=res, res_data=_res_data)
    
    return res, res_data


async def transfer_funds(from_proxy, to_proxy, amount, reason = "10",
                         comment = "Funds transfer"):
    endpoint = _get_call_uri("CO_Acct2AcctTransferFunds.asp")
    data = _get_base_dict_param()
    data['SenderProxyKey'] = from_proxy
    data['ReceiverProxyKey'] = to_proxy
    data['curAmount'] = amount
    data['intReason'] = reason
    data['strComment'] = comment

    res, res_data = await _do_request(endpoint, data)
    logger.warning("#### transfer_funds --> ", res=res, res_data=res_data)

    return res, res_data


async def change_proxy_pin(proxy, newpin):
    endpoint = _get_call_uri("CO_ChangePin_ByProxy.asp")
    data = _get_base_dict_param()
    data['proxykey'] = proxy
    data['NewPIN'] = newpin

    res, res_data = await _do_request(endpoint, data)
    return res, res_data


async def proxy_load_value(proxy, amount):
    endpoint = _get_call_uri("CO_LoadValue_ByProxy.asp")
    data = _get_base_dict_param()
    data['proxykey'] = proxy
    data['amount'] = amount

    res, res_data = await _do_request(endpoint, data)
    return res, res_data


async def proxy_adjust_value(proxy, amount, adjustment_type, comment):
    endpoint = _get_call_uri("CO_AdjustValue.asp")
    data = _get_base_dict_param()
    data['proxykey'] = proxy
    data['adjtype'] = adjustment_type
    data['amount'] = amount
    data['comment'] = comment

    res, res_data = await _do_request(endpoint, data)
    return res, res_data


async def change_proxy_status(proxy, new_status):
    endpoint = _get_call_uri("CO_StatusAcct.asp")
    data = _get_base_dict_param()
    data['ProxyKey'] = proxy
    data['status'] = new_status

    res, res_data = await _do_request(endpoint, data)
    return res, res_data