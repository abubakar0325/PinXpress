
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.conf import settings  # add this import at top
import uuid
from django.utils.timezone import now

class CustomUser(AbstractUser):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    address = models.TextField()
    phone_number = models.CharField(max_length=15, unique=True)
    nin_or_bvn = models.CharField(max_length=20, unique=True)
    email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return self.username
    

class ExamPin(models.Model):
    CARD_CHOICES = [
        ('WAEC Scratch Card', 'WAEC Scratch Card'),
        ('NECO TOKEN', 'NECO TOKEN'),
        ('NABTEB Scratch Card', 'NABTEB Scratch Card'),
        ('WAEC Verification Pin', 'WAEC Verification Pin'),
        ('NBAIS Scratch Card', 'NBAIS Scratch Card'),
        ('WAEC GCE Registration Card', 'WAEC GCE Registration Card'),
        ('NECO e-VERIFICATION PIN', 'NECO e-VERIFICATION PIN'),
        ('EXAMINIFY BIOMETRIC TOKEN', 'EXAMINIFY BIOMETRIC TOKEN'),
    ]

    name = models.CharField(max_length=50, choices=CARD_CHOICES)
    pin = models.CharField(max_length=100)
    serial = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    is_used = models.BooleanField(default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.get_name_display()} - {self.pin}"
class DataCoupon(models.Model):
    network = models.CharField(max_length=20)  # MTN, Glo, etc.
    amount = models.CharField(max_length=10)
    code = models.CharField(max_length=100)
    is_used = models.BooleanField(default=False)




class TopUpTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    successful = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            today = now().strftime('%Y%m%d%H%M%S')
            self.transaction_id = f"TXN-{today}-{self.user.username.upper()[:5]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_id} - {self.user.username} - ₦{self.amount}"
    

class PurchaseTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    
    product = models.CharField(max_length=100)      # e.g. "WAEC Exam Pin" or "NECO Exam Pin"
    quantity = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    
    product_type = models.CharField(max_length=20)
    product_id = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            today = now().strftime('%Y%m%d%H%M%S')
            self.transaction_id = f"PUR-{today}-{self.user.username.upper()[:5]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.transaction_id

