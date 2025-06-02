from django.contrib import admin
from .models import VirtualAccount

@admin.register(VirtualAccount)
class VirtualAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_number', 'bank_name', 'status')
    search_fields = ('user__username', 'account_number', 'bank_name')
