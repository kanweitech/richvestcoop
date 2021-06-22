from re import search
from rest_framework import serializers
from acctmang.models import User, Token
from django.contrib.auth import authenticate


# USER SERIALIZER


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "phone_number", "first_name", "last_name", "nuban", "image_url")



# REGISTER SERIALIZER
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "phone_number", "first_name", "last_name", "password")
        extra_kwargs = {
            "password": {"write_only": True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user



# LOGIN SERIALIZER
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        else:
            raise serializers.ValidationError("Incorrect login credentials")



# EMAIL AUTH SERIALIZER
class PhoneAuthSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


# VERIFY EMAIL AUTH
class VerifyAuthSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    auth_code = serializers.CharField()


class TxRefSerializer(serializers.Serializer):
    """
    Checks and Verify txref success for Flutterwave.
    """

    txref = serializers.CharField()
    transaction_type = serializers.CharField()


class UpdatePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()
    confirm_new_password = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class UpdateForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    auth_code = serializers.CharField()
    new_password = serializers.CharField()
    confirm_new_password = serializers.CharField()


class UpdateProfileImageSerializer(serializers.Serializer):
    image_url = serializers.URLField()


class BankAccountValidateSerializer(serializers.Serializer):
    bankName = serializers.CharField()
    bankAccount = serializers.CharField()
    customerName = serializers.CharField(allow_blank=True)