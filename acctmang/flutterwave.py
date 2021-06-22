# import re
# import os
# from rave_python import Rave
# from rave_python import RaveExceptions 

# Check Card Type Function
# def checkCardType(number):
#     if re.search(r"^4[0-9]{12}(?:[0-9]{3})?$", number):
#         return "Visa"
#     if re.search(r"^((506(0|1))|(507(8|9))|(6500))[0-9]{12,15}$", number):
#         return "Verve"
#     if re.search(r"^(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}$", number):
#         return "Mastercard"


# Change rave PUBK and SECK to environment variables before shipping to production
# rave = Rave(os.environ["RAVE_PUBLIC_KEY"], os.environ["RAVE_SECRET_KEY"], usingEnv=True)