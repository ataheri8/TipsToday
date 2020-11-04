"""

Document that will outline the FIS POST call that will be made
when each card is created, or assigning a pre-existing card to
a user, while also loading in funds directly without any other
call required.

Required fields:
UserID
PWD
SourceID
SubProgID
PackageID
PersonID
LoadAmount
CardType


Conditional fields:
ClientID - Not required if using CardNum or creating a new card
PrimaryCard - Can provide card number to assign pre-allocated card or leave blank for new card generation
PrimaryProxyKey - Proxy Number associated to the primary PAN or CAN. Used with ClientID
ProxyType - Only applicable if proxy number is provided. Not recommended to fill in per document standards,
            only to be used if client uses multiple proxy types in their hierarchy


All calls start with the following syntax:

Insert URL Here/a2a/CO_AssignCard_LoadValue.asp
POST /A2A/CO_AssignCard_LoadValue HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Content-Length: xx
"""

"""
basic call to assign pre-allocated card to a person and load it.

personID: johndoe123
cardtype: 1
PrimaryCard: 4444440010131628
LoadAmount: 50
fees: 1.50
"""

# userid=********&pwd=********&sourceid=********&resp=xml&personid=johndoe123&subprogid=*****&
# PackageID=*****&Cardtype=1&PrimaryCard=4444440010131628&LoadAmount=50&fees=SERVICE FEE|1.50


# Resulting output:
# <r:ROOT Response=""1"" ErrorNumber=""0"" ErrorDescription="""" ErrorDisplay=""1""">
# <r:ROW Cardnum=""***************1"" TxnLogID="""" ConfirmCode="""" RetreivalRefNo=""CC000B287054"" ProxyKey=""*************"" />
# </r:ROOT>"
