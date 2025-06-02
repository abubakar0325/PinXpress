from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class ExamCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class PastQuestion(models.Model):
    category = models.ForeignKey(ExamCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")  # updated here
    price = models.DecimalField(max_digits=8, decimal_places=2)
    file = models.FileField(upload_to='past_questions/')
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.title

# pastquestions/models.py

class Purchase(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(PastQuestion, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    payment_reference = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='paid')
    timestamp = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.username} - {self.question.title}"


class PurchaseTransaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='purchase_transactions_pastquestions'  # simple, unique related_name
    )
    question = models.ForeignKey(PastQuestion, on_delete=models.CASCADE)
    payment_reference = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    purchased_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.question.title}"
