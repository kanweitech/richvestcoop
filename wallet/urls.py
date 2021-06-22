from django.urls import path
from django.urls.conf import path, include

app_name = "wallet"

urlpatterns = [
    path('v1/', include(('wallet.api.v1.urls', app_name), namespace="v1")),
]