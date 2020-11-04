from requests_pkcs12 import post
from requests import get
import json
from datetime import datetime

url = "http://dev.80eight.ca:10001/log/transactions/"
headers = {'content-type': 'application/json'}


def check_response(status_code):
    if status_code == 200:
        return "Success!", status_code
    elif status_code == 422:
        return "Invalid parameter", status_code
    else:
        return "Error", status_code


async def post_card_transaction(amount: float, type: int, proxy: str,
                                user_id: str, person_id: str, client_id: str):
    call = "Transaction"

    data = {"transaction": {
                "amount": amount,
                "type": type,
                "proxy": proxy,
                "user_id": user_id,
                "person_id": person_id,
                "client_id": client_id
    }
    }

    data = json.dumps(data)

    r = post('{}{}'.format(url, call), data=data, headers=headers)

    return check_response(r.status_code)


async def post_wallet_transaction(amount: float, type: int, proxy: str,
                                  wallet_id: str, client_id: str):
    call = "walletTransaction"

    data = {"transaction": {
                "amount": amount,
                "type": type,
                "proxy": proxy,
                "wallet_id": wallet_id,
                "client_id": client_id
    }
    }

    data = json.dumps(data)

    r = post('{}{}'.format(url, call), data=data, headers=headers)

    return check_response(r.status_code)


async def get_transactions(startingDate: str, endingDate: str):
    call = "transactions"

    try:
        clean_startingDate = datetime.strptime(startingDate, "%Y-%m-%d")
        clean_endingDate = datetime.strptime(endingDate, "%Y-%m-%d")
    except:
        return "Date invalid or improper format"

    data = {"StartingDate": startingDate, "EndingDate": endingDate}

    r = get(url=(url + call), params=data)

    return check_response(r.status_code)


async def get_transactions_by_client_id(startingDate: str, endingDate: str, client_id: str):
    call = "transactionsByClientId"

    try:
        clean_startingDate = datetime.strptime(startingDate, "%Y-%m-%d")
        clean_endingDate = datetime.strptime(endingDate, "%Y-%m-%d")
    except:
        return "Date invalid or improper format"

    data = {"StartingDate": startingDate, "EndingDate": endingDate, "client_id": client_id}

    r = get(url=(url + call), params=data)

    return check_response(r.status_code)


async def get_transactions_by_user_id(startingDate: str, endingDate: str, user_id: str):
    call = "transactionsByUserId"

    try:
        clean_startingDate = datetime.strptime(startingDate, "%Y-%m-%d")
        clean_endingDate = datetime.strptime(endingDate, "%Y-%m-%d")
    except:
        return "Date invalid or improper format"

    data = {"StartingDate": startingDate, "EndingDate": endingDate, "client_id": user_id}

    r = get(url=(url + call), params=data)

    return check_response(r.status_code)


async def get_wallet_transactions_by_client_id(startingDate: str, endingDate: str, client_id: str):
    call = "walletTransactionsByClientId"

    try:
        clean_startingDate = datetime.strptime(startingDate, "%Y-%m-%d")
        clean_endingDate = datetime.strptime(endingDate, "%Y-%m-%d")
    except:
        return "Date invalid or improper format"

    data = {"StartingDate": startingDate, "EndingDate": endingDate, "client_id": client_id}

    r = get(url=(url + call), params=data)

    return check_response(r.status_code)


async def get_card_statuses():
    call = "cardStatuses"

    r = get(url=(url + call))

    return check_response(r.status_code)


async def get_wallet_statuses():
    call = "walletStatuses"

    r = get(url=(url + call))

    return check_response(r.status_code)
