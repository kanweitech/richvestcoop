import decimal
import random
import uuid
from django.urls import conf
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer, LoginSerializer, RegisterSerializer
from .serializers import PhoneAuthSerializer, VerifyAuthSerializer, TxRefSerializer
from .serializers import UpdatePasswordSerializer, ForgotPasswordSerializer, UpdateForgotPasswordSerializer, UpdateProfileImageSerializer
from .serializers import BankAccountValidateSerializer
from acctmang.paystack import PaystacksApiChecker
from acctmang.models import PhoneAuth, User, Token, UserBank
# from wrent_savings.models import Savings, SavingsPlan
from acctmang.checkers import check_number, get_bank_name, get_cosine_similarity
# from acctmang.flutterwave import rave
from acctmang.errors import ErrorHandlingCard
from acctmang.tasks import reserve_nuban

# from richvestcoop.settings import twilio_client
from knox.models import AuthToken
from django.utils import timezone
# from richvestcoop.mailer import Mailer
# mail = Mailer()



# REGISTER API
class RegisterAPI(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Call Providus Bank API -> Get User Dedicated Account Number
        reserve_nuban.delay(id=user.id, customer_email=user.email, customer_name=f"{user.first_name} {user.last_name}")
        
        AuthToken_Query = str(AuthToken.objects.create(user))
        AuthToken_Query = AuthToken_Query[1:][:-1]
        AuthToken_Query = AuthToken_Query.split()
        Auth_token = AuthToken_Query[4].strip("\'")

        return Response(
            {
                "status": "success",
                "message": "Account created",
                "user": UserSerializer(
                    user, context=self.get_serializer_context()
                ).data,
                "token": Auth_token

            }
        )

    


class LoginAPI(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        AuthToken_Query = str(AuthToken.objects.create(user))
        AuthToken_Query = AuthToken_Query[1:][:-1]
        AuthToken_Query = AuthToken_Query.split()
        Auth_token = AuthToken_Query[4].strip("'")

        return Response(
            {
                "user": UserSerializer(
                    user, context=self.get_serializer_context()
                ).data,
                "token": Auth_token,
            }
        )


# GET USER API
class UserAPI(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user



# EMAIL AUTH API
class PhoneAuthAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PhoneAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone_number = serializer.data["phone_number"]
        phone_number  = check_number(phone_number)

        if phone_number:

            if User.objects.filter(phone_number=phone_number).exists():
                return Response({
                "status": "error",
                "message": "User account exist",
            }, status.HTTP_406_NOT_ACCEPTABLE)
            

            auth_code = random.randrange(112399, 999999)

            PhoneAuth.objects.update_or_create(
                phone=phone_number, defaults={"auth_code": auth_code}
            )

            message = twilio_client.messages.create(
                body="Richvestcoop Authentication code: {}".format(auth_code),
                from_="+15138132347",
                to=phone_number
            )

            return Response({
                "status": "success",
                "message": "proceed",
                "otp": auth_code
            })

        else:
            return Response({
                "status": "error",
                "message": "Valid Phone number should be provided",
            }, status=status.HTTP_412_PRECONDITION_FAILED)



# VERIFY AUTH CODE
class AuthCodeAPI(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = VerifyAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_code = serializer.data["auth_code"]
        phone_number = serializer.data["phone_number"]

        phone_number  = check_number(phone_number)


        try:
            user = PhoneAuth.objects.filter(phone=phone_number, expired=False).last()
        except PhoneAuth.DoesNotExist:
            user = None

        if user:
            if user.auth_code == auth_code:
                user.expired = True
                user.save(update_fields=["expired"])

                return Response(
                    {"status": "success", "message": "Auth code Success"},
                    status=status.HTTP_200_OK,
                )

            else:
                return Response(
                    {"status": "failed", "message": "Auth code incorrect"},
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                ) 

        else:
            return Response(
                {"status": "failed", "message": "Look up Error. Phone not recognized not recognized."},
                status=status.HTTP_400_BAD_REQUEST,
            ) 


# CHECK TXREF
class TxrefAPI(APIView):
    """
    API view to Check and Verify txref success for Flutterwave Payment.

    Expected fields:
    1. `txref` : str
    2. `transaction_type` : str [Enum: ("savings", "deposit")]  
    """

    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request, *args, **kwargs):
        serializer = TxRefSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data_bank = serializer.data
        txref = data_bank["txref"]
        transaction_type = data_bank["transaction_type"]
        


        user = self.request.user

        res = rave.Card.verify(txref)
        amount = res["amount"]
        card_token = res["cardToken"]

        if res["transactionComplete"]:
            action = Token(user=user, charge_token=card_token)
            action.save()

            # PROCESS TRANSACTION TYPE
            if transaction_type == "savings":
                transaction_time = timezone.now()

                try: 
                    uuid.UUID(txref)
                except ValueError:
                    return Response({
                        "status": "failed",
                        "message": "Plan ID not found",
                    }, status=status.HTTP_412_PRECONDITION_FAILED)


                try:
                    plan_in_view = SavingsPlan.objects.get(plan_id=txref)

                except SavingsPlan.DoesNotExist:
                    return Response({
                        "status": "failed",
                        "message": "Plan ID not found",
                    }, status=status.HTTP_412_PRECONDITION_FAILED)

                if plan_in_view.amount_payable == (decimal.Decimal("{:.2f}".format(amount))):
                    if plan_in_view.paid != True:
                        # Update plan_in_view ==> if state is not true
                        # Otherwise send default success
                        
                        plan_in_view.paid =  True
                        plan_in_view.payment_date = transaction_time

                        plan_in_view.save(update_fields=["paid", "payment_date"])

                        wrent_plan =  Savings.objects.get(wrent_id=plan_in_view.wrent_record.wrent_id)
                        wrent_plan.amount_cleared = (wrent_plan.amount_cleared + plan_in_view.amount_payable)
                        wrent_plan.modified = transaction_time


                        wrent_plan.save(update_fields=["amount_cleared", "modified"])


                    return Response({
                        "status":  "success",
                        "message": "Payment Verified code"
                    }, status=status.HTTP_200_OK)

                else:
                    return Response({
                        "status": "failed",
                        "message": "Amount mismatch",
                    }, status=status.HTTP_412_PRECONDITION_FAILED)
            else:
                return Response({
                        "status": "failed",
                        "message": "Invalid Transaction Type",
                    }, status=status.HTTP_412_PRECONDITION_FAILED)

        else:
            return Response({
                "status": "failed",
                "message": "Error linking card",
                "errros": ErrorHandlingCard("Error linking card")
            }, status=status.HTTP_412_PRECONDITION_FAILED)



# Update Password
class UpdatePasswordAPI(APIView):

    """
    Update Known User Password.

    Expected fields:
    1. `current_password` : *str*

    2. `new_password` : *str* 

    3. `confirm_new_password` : *str*


    Password length: [Min 8 Characters]

    """
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request, *args, **kwargs):
        serializer = UpdatePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data_bank = serializer.data

        current_password = data_bank["current_password"]
        new_password = data_bank["new_password"]
        confirm_new_password = data_bank["confirm_new_password"]

        user = self.request.user

        if user.check_password(current_password):
            if new_password == confirm_new_password:
                if len(new_password) >= 8:
                    user.set_password(new_password)
                    user.save(update_fields=["password"])
                    return Response({
                        "status": "success",
                        "message": "Password updated successfully",
                    })
                else:
                    return Response({
                        "status": "failed",
                        "message": "Password must be at least 8 characters",
                    }, status=status.HTTP_412_PRECONDITION_FAILED)
            else:
                return Response({
                    "status": "failed",
                    "message": "Confirm Password must be the same",
                }, status=status.HTTP_412_PRECONDITION_FAILED)

        else:
            return Response({
                "status": "failed",
                "message": "Incorrect Password",
            }, status=status.HTTP_412_PRECONDITION_FAILED)




class UpdateProfileImageAPI(APIView):

    """
    Update User Profile Image URL

    Expected fields:
    1. `image_ulr` : [ *str*, *url*]


    **Expecting a valid URL string**

    """
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request, *args, **kwargs):
        serializer = UpdateProfileImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image_url = serializer.data["image_url"]

        user = self.request.user

        user.image_url = image_url
        user.save(update_fields=["image_url"])

        return Response({
            "status": "success",
            "message": "Profile Picture updated successfully",
            "image_url": image_url
        })


class ForgotPasswordAPI(APIView):
    """
    Sends OTP verification Mail to User

    Expected fields:
    1. `user_email` : *str*
    """

    permission_classes = [
        permissions.AllowAny
    ]

    def post(self, request, *args, **kwargs):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_email = serializer.data["email"]

        try:
            user_in_view = User.objects.get(email=user_email)

            auth_code = random.randrange(112399, 999999)

            PhoneAuth.objects.update_or_create(
                phone=user_in_view.phone_number, expired=False, defaults={"auth_code": auth_code}
            )


            mail.send_messages(
                subject="Wrent OTP",
                template="emails/authenticate_code.html",
                context={
                    "first_name": f"{user_in_view.first_name}",
                    "auth_code": auth_code,
                    "email": user_in_view.email
                },
                to_emails=[user_in_view.email],
                from_email="Wrent Support <support@wrent.ng>"
            )

            return Response({
                "status": "success",
                "message": "OTP has been sent to registered mail. Proceed to creating new Password"
            })

        except User.DoesNotExist:
            # Fake Response
            return Response({
                "status": "success",
                "message": "OTP has been sent to registered mail. Proceed to creating new Password"
            })



class ResetForgotPasswordAPI(APIView):
    """
    Resets Password for Unauthenticated User

    Expected fields:
    1. `email` : *str*

    2. `auth_code` : *str*

    3. `new_password`: *str*

    4. `confirm_new_password`: *str*
    """

    permission_classes = [
        permissions.AllowAny
    ]

    def post(self, request, *args, **kwargs):
        serializer = UpdateForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data_bank = serializer.data

        user_email = data_bank["email"]
        auth_code = data_bank["auth_code"]
        new_password = data_bank["new_password"]
        confirm_new_password = data_bank["confirm_new_password"]

        try:
            user_in_view = User.objects.get(email=user_email)
        
        except User.DoesNotExist:
            # Fake Response
            return Response({
                "status": "failed",
                "message": "Incorrect auth_code -"
            }, status=status.HTTP_412_PRECONDITION_FAILED)

        try:
            phone_auth_record = PhoneAuth.objects.filter(phone=user_in_view.phone_number, expired=False).last()
            if phone_auth_record.auth_code == auth_code:
                # Check Password
                if new_password == confirm_new_password:
                    if len(new_password) >= 8:
                        user_in_view.set_password(new_password)
                        user_in_view.save(update_fields=["password"])
                        return Response({
                            "status": "success",
                            "message": "Password updated successfully",
                        })
                    else:
                         return Response({
                            "status": "failed",
                            "message": "Password must be at least 8 characters",
                        }, status=status.HTTP_412_PRECONDITION_FAILED)
                        
                else:
                    return Response({
                        "status": "failed",
                        "message": "Confirm Password must be the same",
                    }, status=status.HTTP_412_PRECONDITION_FAILED)

            else:
                return Response({
                    "status": "failed",
                    "message": "Incorrect auth_code --"
                }, status=status.HTTP_412_PRECONDITION_FAILED)

        except PhoneAuth.DoesNotExist:
            return Response({
                "status": "failed",
                "message": "Incorrect auth_code ---"
            }, status=status.HTTP_412_PRECONDITION_FAILED)



class GetBankAccountAPI(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_bank = UserBank.objects.filter(user=self.request.user)

        if len(user_bank) == 0:
            return Response(
                {"status": "failed", "message": "No linked bank account"},
                status=status.HTTP_404_NOT_FOUND,
            )
        else:
            return Response(
                {
                    "status": "success",
                    "data": {
                        "bank_name": get_bank_name(user_bank[0].bank_name),
                        "bank_account_number": user_bank[0].bank_account_number,
                    },
                },
                status=status.HTTP_200_OK,
            )


class BankAccountValidateAPI(APIView):
    """
    Validates Bank account (NUBAN)

    Expected Fields:
    1. `bankName`: [*str, number*]

    2. `bankAccount`: [*str, number*]

    """
    permission_classes = [
        permissions.IsAuthenticated
    ]

    def post(self, request, *args, **kwargs):
        serializer = BankAccountValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bank_code = serializer.data["bankName"]
        account_number = serializer.data["bankAccount"]
        link = "https://api.paystack.co/bank/resolve?account_number={}&bank_code={}".format(
            account_number, bank_code)
        result = PaystacksApiChecker(link).validate_account()

        return Response(result)



class UpdateBankAccountAPI(APIView):

    """
    Create or Updates User Bank Account Information

    Expected Fields:
    1. `bankName`: [*str, number*]

    2. `bankAccount`: [*str, number*]

    3. `customerName`: *str*

    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = BankAccountValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        bank_code = serializer.data["bankName"]
        account_number = serializer.data["bankAccount"]
        customer_account_name = serializer.data["customerName"]

        #Bank Name vs User Registered Name
        similarity = get_cosine_similarity(f"{self.request.user.first_name} {self.request.user.last_name}", customer_account_name)

        if float(similarity) < 0.8:
            return Response({
                "status": "failed",
                "message": "Registered Name and Bank Name does not match"
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        
        else:

            user_bank = UserBank.objects.filter(user=self.request.user)
            if len(user_bank) == 0:
                UserBank.objects.create(
                    user=self.request.user,
                    bank_name=bank_code,
                    bank_name_raw=get_bank_name(bank_code),
                    bank_account_number=account_number,
                    customer_account_name=customer_account_name,
                )

                return Response(
                    {"status": "success", "message": "Bank details successfully saved"},
                    status=status.HTTP_200_OK,
                )
            else:
                user_bank = user_bank.first()
                user_bank.bank_name = bank_code
                user_bank.bank_account_number = account_number
                user_bank.bank_name_raw = get_bank_name(bank_code)
                user_bank.customer_account_name = customer_account_name

                user_bank.save(
                    update_fields=[
                        "bank_name",
                        "bank_account_number",
                        "bank_name_raw",
                        "customer_account_name",
                    ]
                )

                return Response(
                    {
                        "status": "success", 
                        "message": "Bank details successfully saved",
                        "data": {
                        "bank_name": get_bank_name(user_bank.bank_name),
                        "bank_account_number": user_bank.bank_account_number,
                    },
                        },
                    status=status.HTTP_200_OK,
                )