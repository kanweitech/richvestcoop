import os
import requests
import hashlib


class ProvidusBank(object):
    """
    Providus Bank Virtual Payment Service Object
    """

    def __init__(self, base_url=os.environ["PROVIDUS_BASE_URL"]):
        self.base_url = base_url

    
    def generate_auth_signature(self) -> str:
        string_in_view = "{}:{}".format(os.environ["PROVIDUS_CLIENT_ID"], os.environ["PROVIDUS_CLIENT_SECRET"])
        string_in_view = string_in_view.encode("utf-8")
        hashed = hashlib.sha512(string_in_view)

        return hashed.hexdigest()

    def reserve_account(self, account_name):
        reserve_response = requests.post(f"{self.base_url}/PiPCreateReservedAccountNumber", json={
            "account_name": account_name,
            "bvn": ""
        }, headers={"Content-Type": "application/json", "Client-Id": os.environ["PROVIDUS_CLIENT_ID"], "X-Auth-Signature": os.environ["PROVIDUS_SIGNATURE_SHA512"]})


        return reserve_response.json()