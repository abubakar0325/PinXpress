
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User


User = get_user_model()

class MonnifyVirtualAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=20, unique=True)
    bank_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.account_number}"

class MonnifyTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20)  # e.g., 'SUCCESS', 'FAILED', 'PENDING'
    transaction_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_reference} - {self.status}"


class VirtualAccount(models.Model):
    user = user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='virtual_account')
    account_reference = models.CharField(max_length=255, unique=True)
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=255)
    bank_code = models.CharField(max_length=20)
    status = models.CharField(max_length=50)
    reservation_reference = models.CharField(max_length=255)
    bvn = models.CharField(max_length=20, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username} - {self.account_number}"
