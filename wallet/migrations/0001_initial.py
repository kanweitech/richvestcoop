# Generated by Django 3.2.4 on 2021-06-22 08:23

from decimal import Decimal
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wallet_id', models.CharField(max_length=100, unique=True, verbose_name='Wallet ID')),
                ('created', models.DateTimeField(blank=True)),
                ('modified', models.DateTimeField(blank=True)),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='Wallet Balance')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='wallets', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Wallet',
                'verbose_name_plural': 'Wallets',
            },
        ),
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uidref', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Transaction identifier')),
                ('ttype', models.CharField(choices=[('CREATED', 'Created'), ('DEPOSIT', 'Deposit'), ('WITHDRAW', 'Withdraw')], max_length=30)),
                ('timestamp', models.DateTimeField(blank=True)),
                ('delta', models.DecimalField(decimal_places=2, max_digits=12)),
                ('debug_balance', models.DecimalField(decimal_places=2, help_text='Balance after user action', max_digits=12)),
                ('meta_info', models.TextField(blank=True, editable=False, max_length=200)),
                ('user', models.ForeignKey(help_text='User who performed the action.', on_delete=django.db.models.deletion.PROTECT, related_name='actions', to=settings.AUTH_USER_MODEL)),
                ('wallet', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='wallets', to='wallet.wallet')),
            ],
            options={
                'verbose_name': 'Wallet action',
                'verbose_name_plural': 'Wallet actions',
            },
        ),
    ]
