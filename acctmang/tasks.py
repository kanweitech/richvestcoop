import os, requests, decimal
from .providus import ProvidusBank
from .models import User
from wallet.models import Wallet
from richvestcoop.celery import app
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@app.task(name="acctmang.reserve_nuban_task")
def reserve_nuban(id, customer_email, customer_name, account_reference=None):
    try:
        user = User.objects.get(pk=id)
        nuban_reserve =  ProvidusBank().reserve_account(account_name=customer_name)
        if nuban_reserve["requestSuccessful"] == True:
            user.nuban = nuban_reserve["account_number"]
            user.save(update_fields=["nuban"])
        else:
            logger.info(f"Providus Account Reserve Error for {customer_name}:{id}")
    except User.DoesNotExist:
        logger.info(f"Customer UID non-existent: {account_reference}")