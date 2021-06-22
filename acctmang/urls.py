from django.urls import path
from django.urls.conf import path, include

app_name = "acctmang"

urlpatterns = [
    path('v1/', include(('acctmang.api.v1.urls', app_name), namespace="v1")),
]