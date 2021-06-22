from django.db import models, transaction
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import ugettext_lazy as _

import uuid
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from .errors import InvalidAmount, InsufficientFunds, UserDoesNotExist
from django.core.exceptions import ObjectDoesNotExist



class Wallet(models.Model):
	class Meta:
		verbose_name = "Wallet"
		verbose_name_plural = "Wallets"

	MIN_BALANCE = 0.00

	user = models.OneToOneField(
		settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="wallets"
	)

	wallet_id = models.CharField(_("Wallet ID"), unique=True, max_length=100)

	created = models.DateTimeField(blank=True)

	modified = models.DateTimeField(blank=True)

	balance = models.DecimalField(
		_("Wallet Balance"),
		default=0,
		max_digits=12,
		decimal_places=2,
		validators=[
			MinValueValidator(Decimal("0.00")),
		]
	)

	@classmethod
	def create(cls, user, asof):
		"""
		Create wallet.
		user (User):
		owner of the wallet.

		Returns (tuple):
			[0] Wallet
			[1] Action
		"""

		with transaction.atomic():
			wallet = cls.objects.create(
				user=user,
				created=asof,
				modified=asof,
			)

			action = Action.create(
				user=user,
				wallet=wallet,
				ttype=Action.ACTION_TYPE_CREATED,
				delta=0,
				asof=asof,
			)
		return wallet, action

	@classmethod
	def deposit(cls, wallet_id, received_by, amount, asof, meta_info):

		assert amount > 0

		with transaction.atomic():
			wallet = cls.objects.select_for_update().get(wallet_id=wallet_id)

			wallet.balance += amount
			wallet.modified = asof

			wallet.save(
				update_fields=[
					"balance",
					"modified",
				]
			)

			action = Action.create_deposit(
				user=received_by,
				wallet=wallet,
				ttype=Action.ACTION_TYPE_DEPOSIT,
				delta=amount,
				asof=asof,
				meta_info=meta_info,
			)
		return wallet, action

class Action(models.Model):
	class Meta:
		verbose_name = "Wallet action"
		verbose_name_plural = "Wallet actions"

	ACTION_TYPE_CREATED = "CREATED"
	ACTION_TYPE_DEPOSIT = "DEPOSIT"
	ACTION_TYPE_WITHDRAW = "WITHDRAW"

	ACTION_TYPE_CHOICES = (
		(ACTION_TYPE_CREATED, "Created"),
		(ACTION_TYPE_DEPOSIT, "Deposit"),
		(ACTION_TYPE_WITHDRAW, "Withdraw"),
	)

	uidref = models.UUIDField(
		unique=True,
		editable=False,
		default=uuid.uuid4,
		verbose_name="Transaction identifier"
	)

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		related_name="actions",
		on_delete=models.PROTECT,
		help_text="User who performed the action.",
	)

	ttype = models.CharField(
		max_length=30,
		choices=ACTION_TYPE_CHOICES,
	)

	timestamp = models.DateTimeField(blank=True)

	wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="wallets")

	delta = models.DecimalField(
		max_digits=12,
		decimal_places=2
	)

	# debugging purposes
	debug_balance = models.DecimalField(
		max_digits=12,
		decimal_places=2,
		help_text="Balance after user action"
	)

	meta_info = models.TextField(max_length=200, blank=True, editable=False)

	

	@classmethod
	def create(cls, user, wallet, ttype, delta, asof):
		"""
		Create Action.
		user (User):
			User who executed the action.
		wallet (Wallet):
			Wallet the action is executed on.
		ttype (str, one of Action.ACTION_TYPE_*):
			Transaction type or action type.
		delta(float):
			change in balance.
		uidref and timestamp are auto generated.

		Returns (Action)
		"""

		# validation errors can be humbly raised here, with:
		# from django.core.exceptions import ValidationError

		return cls.objects.create(
			timestamp=asof,
			user=user,
			wallet=wallet,
			ttype=ttype,
			delta=delta,
			debug_balance=wallet.balance,
			meta_info="New Account: Account Activation",
		)

	@classmethod
	def create_deposit(cls, user, wallet, ttype, delta, asof, meta_info):
		"""
		Records user deposit transaction

		"""

		return cls.objects.create(
			timestamp=asof,
			user=user,
			wallet=wallet,
			ttype=ttype,
			delta=delta,
			debug_balance=wallet.balance,
			meta_info=meta_info,
		)
