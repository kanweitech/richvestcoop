from django.urls import path
from .api import UserAPI, LoginAPI, RegisterAPI, PhoneAuthAPI, AuthCodeAPI, TxrefAPI
from .api import UpdatePasswordAPI, UpdateProfileImageAPI, ForgotPasswordAPI, ResetForgotPasswordAPI
from .api import BankAccountValidateAPI,  GetBankAccountAPI, UpdateBankAccountAPI
# from knox import views as knox_views


urlpatterns= [
    path("auth/register", RegisterAPI.as_view()),
    path("auth/login", LoginAPI.as_view()),
    # path("auth/logout", knox_views.LogoutView.as_view(), name="knox_logout"),
    path("auth/user", UserAPI.as_view()),
    #
    path("phone/verify", PhoneAuthAPI.as_view()),
    path("phone/authchecker", AuthCodeAPI.as_view()),
    #
    path("payment/card/verify", TxrefAPI.as_view()),
    #
    path("profile/update-password", UpdatePasswordAPI.as_view()),
    path("profile/update-profile-image", UpdateProfileImageAPI.as_view()),
    path("profile/forgot-password", ForgotPasswordAPI.as_view()),
    path("profile/forgot-password-update", ResetForgotPasswordAPI.as_view()),
    path("profile/getbank", GetBankAccountAPI.as_view()),
    path("profile/validatebank", BankAccountValidateAPI.as_view()),
    path("profile/updatebank", UpdateBankAccountAPI.as_view()),


]