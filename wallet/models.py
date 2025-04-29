from decimal import Decimal
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.exceptions import ValidationError

from user.models import User
from django.conf import settings

# Create your models here.

class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    account_number = models.CharField(max_length=10, unique=True)

    def deposit(self, amount):
        if amount > Decimal('0.00'):
            self.balance += amount
            self.save()
        return False

    def withdraw(self, amount):
        if amount > Decimal('0.00'):
            self.balance -= amount
            self.save()
            return True
        return False



class Transaction(models.Model):
    TRANSACTION_TYPE = [
        ("D", "DEPOSIT"),
        ("W", "WITHDRAW"),
        ("T", "TRANSFER"),
    ]
    # wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    reference = models.CharField(max_length=40, unique=True)
    transaction_type = models.CharField(max_length=1, choices=TRANSACTION_TYPE, default='D')
    transaction_date = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sender', null=True)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receiver', null=True)
    recipient_account = models.CharField(max_length=15, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.sender is None and self.receiver is None:
            raise ValidationError("Sender and Receiver must be set")
        super().save(*args, **kwargs)