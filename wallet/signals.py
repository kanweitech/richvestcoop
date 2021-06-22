from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Wallet
from acctmang.models import User

@receiver(pre_save, sender=Wallet)
def create_wallet_id(sender, instance, *args, **kwargs):
	if not instance.wallet_id:
		try:
			user = User.objects.get(id=instance.user.id)
			uid = user.email
			instance.wallet_id = uid

		except:
			raise ProcessLookupError("Error creating wallet id")