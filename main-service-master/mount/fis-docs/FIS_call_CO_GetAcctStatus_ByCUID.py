"""

Document that will outline the FIS POST call that will be made
when each card is created, or assigning a pre-existing card to
a user, while also loading in funds directly without any other
call required.

Required fields:

userid
pwd
sourceid
ClientUniqueID
ClientID


All calls start with the following syntax:

Insert URL Here/a2a/CO_GetAcctStatus_ByCUID.asp
POST /A2A/CO_GetAcctStatus_ByCUID.asp HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Content-Length: xx

"""

"""
basic call to retrieve the account status, as defined by FIS 

ClientUniqueID: JABText1234
clientid: ******
"""

# userid=******&pwd=******&sourceid=***&clientuniqueid=JABText1234&resp=xml&clientid=162521

#  "<r:ROOT Response=""1"" ErrorNumber=""0"" ErrorDescription="""" ErrorDisplay=""1"">
#   <r:ROW StatusText=""READY"" LExpdate=""10/13"" />
#   </r:ROOT>"


