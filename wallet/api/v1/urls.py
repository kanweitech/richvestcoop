from django.urls import path
from .api import UserTransactionRecordAPI

urlpatterns= [
    path("wallets/statement", UserTransactionRecordAPI.as_view()),
]