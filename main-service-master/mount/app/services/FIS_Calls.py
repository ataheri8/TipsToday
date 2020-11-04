"""
Document that will outline the FIS POST calls that will be made
"""

from pathlib import Path
from .Sanitize_Calls import *
from requests_pkcs12 import post
import xmltodict
import json
import re

url = "https://a2a.uatfisprepaid.com/a2a/"  # testing url
# url = "https://a2a.fisprepaid.com/"  #production url

USERID = "CArthurA2A"         # This will be the userid associated with FIS
PWD = "H12j2393565110"            # This will be the pwd associated with FIS
SOURCEID = "1234"       # This will be the source ID associated with FIS\
CLIENTID = "184373"     # This is the client's ID required to make the calls
SUBPROGID = "785743"      # This is the sub program ID used to describe card program attributes
PACKAGEID = "707212"      # This is the package ID that describes card fulfillment attributes
CARDTYPE = 1            # This ensures we are only to be working with primary cards, no secondaries
PFX_URL = Path("/srv/root/app/services/recovered-Certificate.pfx").absolute()
PFX_PASSWORD = "SNBDwolU1v0j"

pattern_succ = "^1 .*"
prog = re.compile(pattern_succ)


async def clear_none_values(dictionary):
   return {
      k:v
      for k, v in dictionary.items()
      if v is not None
   }

async def xml_to_dict(xml: str):
    new_dict = dict()
    split = xml.split("</Schema>")
    rows = split[1].replace("#", "").replace("Tran Date", "TranDate")\
                   .replace("Post Date", "PostDate").replace("</XML>", "")\
                   .replace("r:ROW", "Transactions").replace("@", "")

    new_dict = dict(xmltodict.parse(rows))["r:ROOT"]

    final_dict = json.loads(re.sub('@', '', json.dumps(new_dict)))

    if final_dict['Response'] == "1":
        return True, final_dict
    else:
        return False, final_dict


async def create_fis_user(first: str, last: str, ssn: int, address: str,
                        city: str, state: str, zipcode: str, country: str, mi=None, proxykey=None):
    call = "CO_AssignCard.asp"

    data = {"userid": USERID, "pwd": PWD, "sourceid": SOURCEID, "clientid": CLIENTID, "subprogid": SUBPROGID, "pkgid": PACKAGEID,
            "first": first, "last": last, "mi": mi, "ssn": ssn,
            "addr1": address, "city": city, "state": state, "zipcode": zipcode, "country": country, "proxykey": proxykey}

    data = await clear_none_values(data)

    data_check = await create_fis_user_check(**data)

    if True in data_check:
        r = post('{}{}'.format(url, call), data=data,
                 pkcs12_filename=PFX_URL, pkcs12_password=PFX_PASSWORD, allow_redirects=False)
        result = prog.match(r.text)
        if result is not None:
            split = r.text.split(' ')
            return True, split[1].replace('^','')
        return False, r.text
    else:
        return False, data_check


async def activate_card(personid: str, proxykey: int):
    global data, call
    call = "CO_AssignCard2ExistingPerson.asp"
   
    data = {"userid": USERID, "pwd": PWD, "sourceid": SOURCEID, "subprogid": SUBPROGID, "pkgid": PACKAGEID,
            "personid": personid, "clientid": CLIENTID, "ProxyKey": proxykey}

    data_check = await activate_card_check(personid, proxykey)

    if data_check:
        r = post('{}{}'.format(url, call), data=data,
                 pkcs12_filename=PFX_URL, pkcs12_password=PFX_PASSWORD, allow_redirects=False)
        
        result = prog.match(r.text)
        if result is not None:
            split = r.text.split(' ')
            return True, split[1].replace('^','')
        print(r.text)
        return True,r.text
    else:
        return False, data_check


async def check_balance(proxykey: int):
    call = "CO_OTB_ByProxy.asp"

    data = {"userid": USERID, "pwd": PWD, "sourceid": SOURCEID, "subprogid": SUBPROGID, "proxykey": proxykey}

    data_check = await check_balance_check(proxykey)

    if True in data_check:
        r = post('{}{}'.format(url, call), data=data,
                 pkcs12_filename=PFX_URL, pkcs12_password=PFX_PASSWORD, allow_redirects=False)
        result = prog.match(r.text)

        if result is not None:
            split = r.text.split(' ')
            amount = split[1].split('|')
            return True, amount[0]
        else:
            return False, r.text
    else:
        return False, data_check


async def check_status(proxykey: int):
    call = "CO_GetAcctStatus.asp"

    data = {"userid": USERID, "pwd": PWD, "sourceid": SOURCEID, "proxykey": proxykey, "clientid": CLIENTID}

    data_check = await get_acct_status_check(proxykey)

    if True in data_check:
        r = post('{}{}'.format(url, call), data=data,
                 pkcs12_filename=PFX_URL, pkcs12_password=PFX_PASSWORD, allow_redirects=False)
        result = prog.match(r.text)
        if result is not None:
            split = r.text.split(' ')
            return True, split[1].replace('^','')
        return False, r.text
    else:
        return False, data_check


async def change_status(status: str, proxykey : int):
    call = "CO_StatusAcct.asp"

    data = {"userid": USERID, "pwd": PWD, "sourceid": SOURCEID, "clientid": CLIENTID, "status": status, "ProxyKey": proxykey}

    data_check = await change_status_check(status, proxykey)

    if True in data_check:
        r = post('{}{}'.format(url, call), data=data,
                 pkcs12_filename=PFX_URL, pkcs12_password=PFX_PASSWORD, allow_redirects=False)
        result = prog.match(r.text)
        if result is not None:
            split = r.text.split(' ')
            return True, split[1].replace('^','')
        return False, r.text
    else:
        return False, data_check


async def load_value(proxykey: str, loadamount: float):
    
    global data, call
    call = "CO_LoadValue_ByProxy.asp"

    data = {"userid": USERID, "pwd": PWD, "sourceid": SOURCEID, "subprogid": SUBPROGID, "clientid": CLIENTID, "amount": loadamount, "proxykey": proxykey}
    
    data_check = await load_value_check(proxykey, loadamount)

    if True in data_check:
        r = post('{}{}'.format(url, call), data=data,
                 pkcs12_filename=PFX_URL, pkcs12_password=PFX_PASSWORD, allow_redirects=False)
        result = prog.match(r.text)
        if result is not None:
            split = r.text.split(' ')
            return True, split[1].replace('^','')
        return False, r.text
    else:
        return False, data_check


async def change_pin(proxykey: int, newpin="RANDOM"):
    call = "CO_ChangePin_ByProxy.asp"

    data = {"userid": USERID, "pwd": PWD, "sourceid": SOURCEID, "proxykey": proxykey, "NewPIN": newpin}

    data_check = await change_pin_check(proxykey, newpin)

    if True in data_check:
        r = post('{}{}'.format(url, call), data=data,
                 pkcs12_filename=PFX_URL, pkcs12_password=PFX_PASSWORD, allow_redirects=False)
        result = prog.match(r.text)
        if result is not None:
            split = r.text.split(' ')
            return True, split[1].replace('^','')
        return False, r.text
    else:
        return False, data_check


async def create_person(first, last, addr1, city, country, ssn, mi=None):
    call = "CO_CreatePerson.asp"

    data = {"userid": USERID, "pwd": PWD, "sourceid": SOURCEID, "clientid": CLIENTID, "first": first,
            "last": last, "addr1": addr1, "city": city, "country": country, "ssn": ssn, "mi": mi}

    data = await clear_none_values(data)

    data_check = await create_person_check(first, last, addr1, city, country, ssn, mi)

    

    if True in data_check:
        r = post('{}{}'.format(url, call), data=data,
                 pkcs12_filename=PFX_URL, pkcs12_password=PFX_PASSWORD, allow_redirects=False)

        result = prog.match(r.text)
        if result is not None:
            split = r.text.split(' ')
            return True, split[1].replace('^','')
        return False, r.text
    else:
        return False, data_check


async def update_person(personid, first, last):
    call = "CO_UpdatePerson.asp"

    data = {"userid": USERID, "pwd": PWD, "sourceid": SOURCEID, "first": first,
            "last": last, "personid": personid}

    data_check = await update_person_check(first, last, personid)    

    if True in data_check:
        r = post('{}{}'.format(url, call), data=data,
                 pkcs12_filename=PFX_URL, pkcs12_password=PFX_PASSWORD, allow_redirects=False)
        result = prog.match(r.text)
        if result is not None:
            split = r.text.split(' ')
            return True, split[1].replace('^','')
        return False, r.text
    else:
        return False, data_check


async def card_to_card_transfer(sender_proxy, receiver_proxy, amount, intReason = "10", strComment = "transfer funds"):
    call = "CO_Acct2AcctTransferFunds.asp"

    data = {"userid": USERID, "pwd": PWD, "sourceid": SOURCEID, "clientid": CLIENTID, "SenderProxyKey": sender_proxy,
            "ReceiverProxyKey": receiver_proxy, "curAmount": amount, "intReason": intReason, "strComment": strComment}

    data_check = await card_to_card_transfer_check(sender_proxy, receiver_proxy, amount)
    print(data_check)
    if True in data_check:
        r = post('{}{}'.format(url, call), data=data,
                 pkcs12_filename=PFX_URL, pkcs12_password=PFX_PASSWORD, allow_redirects=False)
        result = prog.match(r.text)

        if result is not None:
            return True, r.text
        else:
            return False, r.text
    else:
        return False, data_check


async def get_transactions(proxykey, StartDate = None, Days = None):
    call = "CO_GetCardTxns.asp"

    data = {"userid": USERID, "pwd": PWD, "sourceid": SOURCEID, "clientid": CLIENTID, "ProxyKey": proxykey,
            "StartDate": StartDate, "Days": Days, "resp": "xml"}

    data = await clear_none_values(data)
    
    data_check = await get_transactions_check(proxykey, StartDate, Days)
    
    if True in data_check:
        r = post('{}{}'.format(url, call), data=data,
                 pkcs12_filename=PFX_URL, pkcs12_password=PFX_PASSWORD, allow_redirects=False)
        found, data = await xml_to_dict(r.text)
        if found is False:
            return False, data
        else:
            return True, data
    else:
        return False, data_check