from pathlib import Path
from requests_pkcs12 import post
import re
import asyncio
from app.services import Sanitize_Calls
import urllib3

url = "https://connect.dcbankapi.ca:35345/integrationapi/v1.0/Atm/SearchAtmLocator"
header = {'Content-Type': 'application/json'}
locations = dict()


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # to remove warning message
async def get_atm_locations(latitude: float, longitude: float):

    data = {"latitude": latitude, "longitude": longitude}

    data_check = await Sanitize_Calls.get_atm_locations_check(latitude, longitude)

    if True in data_check:
        r = post('{}'.format(url), json=data, headers=header, verify=False)

        items = r.text.split('{')
        counter = 0

        while counter < 30:
            fields = items[counter + 3].split(":")
            split_lat = fields[7].split(",")
            split_long = fields[8].split(",")
            locations[split_lat[0]] = split_long[0]
            counter += 1
    else: 
        return False, data_check

    return True, locations
