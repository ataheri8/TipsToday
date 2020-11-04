"""

Document that will outline the FIS POST calls that will be made
when each card is created in the database or assigning a pre-existing
card to a user

Required fields:
UserID
PWD
SourceID
First
last
Addr1
City
Country
SSN

Conditional fields:
CardNum - Required if call is made to existing card instead of creating a new one
ProxyKey - Associated with CAN or PAN. Used with ClientID instead of CardNum
ClientID - Not required if using CardNum and using with ProxyKey
SubprogID - Required if cardnum or proxykey is empty. Describes card program attributes
PKGID - Required if cardnum or proxykey is empty. Describes card fulfillment attributes

All calls start with the following syntax:

Insert URL Here/a2a/CO_AssignCard.asp
POST /A2A/CO_AssignCard HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Content-Length: xx
"""

"""
basic call to register a new user to a new card.

Name: John b. Doe
SSN: 999999999
Address: 123 test street
City: Tempe
State: AZ
zipcode: 12345
country: 840 (US default, not sure where to find for Canada)
ShipMethod = 16 (express, by default it is first class)
"""

# userid=*****&pwd=*****&sourceid=**&subprogid=1234&pkgid=5678&clientid=987654&first=John
# &mi=b&last=Doe&SSN=999999999&addr1=123%20Test%20Street&city=Tempe&state=AZ&zipcode=12345&\
# country=840&ShipMethod=16

"""
Resulting output:
1 4444440010131628|123456789|999|11/30/2013 11:59:59 PM|<NULL>|<NULL>|<NULL>|1234561234561^
"""


"""
basic call to register a new user to an existing card.

Name: John b. Doe
SSN: 999999999
Address: 123 test street
City: Tempe
State: AZ
zipcode: 12345
country: 840 (US default, not sure where to find for Canada)
CardNum = 4444440010131628
"""

# userid=*****&pwd=*****&sourceid=**&first=John&mi=b&last=Doe&SSN=999999999&addr1=123%20Test%20Street&\
# city=Tempe&state=AZ&zipcode=12345&country=840&CardNum=4444440010131628

"""
Resulting output:
1 4444440010131628|123456789|999|11/30/2013 11:59:59 PM|<NULL>|<NULL>|<NULL>|1234561234561^
"""