'''Module for working with twilio'''
# -*- coding: utf-8 -*-
import asyncio
import traceback

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.common import logger, settings, errors



def get_client():
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_ACCOUNT_TOKEN)


def send_reset_pass_msg(recipient, token):
    body = f"""Your Tipstoday reset code is: {token}"""

    client = get_client()
    message = client.messages.create(
        to=recipient,
        from_=settings.TWILIO_FROM_NUMEBR,
        body=body
    )

    return message


def validate_number(mobile_number):
    client = get_client()
    try:
        _ = client.lookups.phone_numbers(mobile_number).fetch()
        return True, None

    except TwilioRestException as e:
        logger.warning("Twilio exception: ", traceback=traceback.format_exc(e))
        if e.code == 20404:
            return False, errors.E['customers_phone_number_invalid']
        else:
            return False, errors.E['customers_phone_validation_exception']
