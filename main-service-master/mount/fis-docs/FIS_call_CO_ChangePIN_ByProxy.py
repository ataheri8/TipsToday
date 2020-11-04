"""

Document that will outline the FIS POST call that will be made
when each card is created, or assigning a pre-existing card to
a user, while also loading in funds directly without any other
call required.

Required fields:

userid
pwd
sourceid
proxykey
newPIN

All calls start with the following syntax:

Insert URL Here/a2a/CO_ChangePIN_ByProxy.asp
POST /A2A/CO_ChangePIN_ByProxy.asp HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Content-Length: xx

"""

"""
basic call to set a new pin for an account 

ProxyKey: *****
NewPIN = RANDOM (Used for random pin, can also input a specific pin if needed)
clientid: ******
"""

# userid=*****&pwd=*****&sourceid=**&clientid=987654&proxykey=234561234561&
# NewPIN=RANDOM&reasonid=1286&Comment=TestRandomPin&resp=html&hdr=1


# Resulting output:
# 1 PROXYKEY^1234561234561
