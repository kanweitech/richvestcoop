from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from .checkers import check_number
from django.db.models.signals import post_save
from django.urls import reverse
from decimal import Decimal
from wallet.models import Wallet
from django.utils import timezone

class UserAccountManager(BaseUserManager):

	def _create_user(self, email, phone_number, first_name, last_name, password, **extra_fields):
		checked_phone_number = check_number(phone_number)

		if not email:
			raise ValueError("Email address must be provided")
		if checked_phone_number == False:
			raise ValueError("Valid phone number should be provided")
		if not first_name:
			raise ValueError("First name required")
		if not last_name:
			raise ValueError("Last name is required")
		if not password:
			raise ValueError("password must be provided")

		email = self.normalize_email(email)
		user = self.model(
			email=email,
			phone_number=checked_phone_number,
			first_name=first_name,
			last_name=last_name,
			password=password,
			**extra_fields
		)
		user.set_password(password)
		user.save(using=self.db)

	def create_user(
		self,
		email=None,
		phone_number=None,
		first_name=None,
		last_name=None,
		password=None,
		**extra_fields
	):
		return self._create_user(
			email, phone_number, first_name, last_name, password, **extra_fields
		)

	def create_superuser(self, email, phone_number, first_name, last_name, password, **extra_fields):
		extra_fields["is_staff"] = True
		extra_fields["is_superuser"] = True

		return self._create_user(
            email, phone_number, first_name, last_name, password, **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
	REQUIRED_FIELDS = [
		"phone_number",
		"first_name",
		"last_name",
	]
	USERNAME_FIELD = "email"

	email = models.EmailField("email", unique=True)
	phone_number = models.CharField(max_length=15, unique=True)
	first_name = models.CharField("First Name", max_length=100)
	last_name = models.CharField("Last Name", max_length=100)
	image_url = models.URLField(default="https://res.cloudinary.com/olamigoke/image/upload/v1620480457/Wallet/profile_picture_jb3g6m.png")
	nuban = models.CharField(max_length=20, default="*** *** ***")
	is_staff = models.BooleanField("staff status", default=False)
	is_active = models.BooleanField("active", default=True)

	objects = UserAccountManager()

	def __str__(self):
		return self.email

	def get_fullname(self):
		return "{} {}".format(self.first_name, self.last_name)

def create_wallet(sender, **kwargs):
	if kwargs["created"]:
		user_wallet = Wallet().create(
			user=kwargs["instance"],
			asof=str(timezone.now().strftime("%Y-%m-%d %H:%M:%S")),
		)

post_save.connect(create_wallet, sender=User)

class UserBank(models.Model):
	user = models.OneToOneField(User, on_delete=models.PROTECT, related_name="bank")
	bank_name = models.CharField(max_length=100)
	bank_account_number = models.CharField(max_length=100)
	customer_account_name = models.CharField(max_length=100)

	def __str__(self):
		return "{} {}".format(self.user, self.bank_name)

class Token(models.Model):
	user = models.ForeignKey(
		User, null=True, related_name="tokens", on_delete=models.PROTECT
	)
	card_type = models.CharField(max_length=10)
	card_number = models.CharField(max_length=4)
	expiry_month = models.CharField(max_length=2)
	expiry_year = models.CharField(max_length=2)
	charge_token = models.CharField(max_length=50)

	def __str__(self):
		return str(self.charge_token)

class PhoneAuth(models.Model):
	phone = models.CharField(max_length=50)
	auth_code = models.CharField(max_length=12)
	expired = models.BooleanField(default=False)

	def __str__(self):
		return str(self.phone)

