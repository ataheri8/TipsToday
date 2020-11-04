"""

Document that will outline the FIS POST call that will be made
when each card is created, or assigning a pre-existing card to
a user, while also loading in funds directly without any other
call required.

Required fields:

UserID
PWD
SourceID
Status

Conditional fields:
ClientID - Not required if using CardNum or creating a new card
CardNum - Can provide card number to assign pre-allocated card or leave blank for new card generation
ProxyKey - Proxy Number associated to the primary PAN or CAN. Used with ClientID

All calls start with the following syntax:

Insert URL Here/a2a/CO_StatusAcct.asp
POST /A2A/CO_StatusAcct.asp HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Content-Length: xx

"""

"""
basic call to close an account 

ProxyKey: *****
Status: Close (can also use SUSPEND to just suspend an account instead of closing it)
clientid: ******
"""

# userid=*****&pwd=*****&sourceid=**&clientid="""""&ProxyKey=xxxxxx0000000237&Status=Close&hdr=1&resp=html


# Resulting output:
# 1 STATUS^close^