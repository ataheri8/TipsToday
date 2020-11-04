"""

Document that will outline the FIS POST call that will be made
when loading funds into a card.

Required fields:
UserID
PWD
SourceID
ProxyKey
SubProgID
Amount

All calls start with the following syntax:

Insert URL Here/a2a/CO_LoadValue_ByProxy.asp
POST /A2A/CO_AssignCard HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Content-Length: xx
"""

"""
basic call to load a value into an existing card

proxykey: 1234561234561
subprogid: 123123
purseno: 14
amount: 25

"""

# userid=****&pwd=****&sourceid=****&proxykey=1234561234561&\
# subprogid=123123&purseno=14&amount=25&resp=html&hdr=1

"""
Resulting output:
1 AMOUNT|BALANCE|PROXYKEY|TXNLOGID|RETREIVALREFNO^25|19959.309|1234561234561||CC001BECEB90^	
"""
