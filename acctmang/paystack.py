import os
import requests
from rest_framework.response import Response


class PaystacksApiChecker(object):
    def __init__(self):
    # def __init__(self, url, access_token=os.environ["PAYSTACK_ACCESS_TOKEN"]):
        self.url = url
        self.access_token = access_token

    def validate_account(self):
        step_result = requests.get(self.url,
                                   headers={'Content-Type': 'application/json',
                                            'Authorization': 'Bearer {}'.format(self.access_token)})
        result = step_result.json()
        return result
