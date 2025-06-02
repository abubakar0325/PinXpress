import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project_name.settings')
django.setup()

from products.models import ExamPin

pins = [
    {"name": "WAEC Scratch Card", "pin": "1234567890", "serial": "SN001", "is_used": False},
    {"name": "NECO TOKEN", "pin": "0987654321", "serial": "SN002", "is_used": False},
    {"name": "NABTEB Scratch Card", "pin": "1122334455", "serial": "SN003", "is_used": False},
]

for p in pins:
    ExamPin.objects.create(**p)

print("Test pins added.")
