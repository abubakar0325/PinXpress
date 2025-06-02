from django.contrib import admin


from .models import ExamPin

from .models import CustomUser
from django.contrib.auth.admin import UserAdmin
from .models import TopUpTransaction, PurchaseTransaction
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path
from django.utils.html import format_html
from .models import CustomUser, TopUpTransaction

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'balance', 'email', 'phone_number')
    actions = ['top_up_selected_users']

    def top_up_selected_users(self, request, queryset):
        if 'apply' in request.POST:
            amount = request.POST.get('amount')
            if not amount:
                self.message_user(request, "Please enter a valid amount.", level=messages.ERROR)
                return
            try:
                amount = float(amount)
            except ValueError:
                self.message_user(request, "Invalid amount format.", level=messages.ERROR)
                return
            
            for user in queryset:
                user.balance += amount
                user.save()
                TopUpTransaction.objects.create(user=user, amount=amount, successful=True)
            self.message_user(request, f"Successfully topped up ₦{amount} to {queryset.count()} users.")
            return redirect(request.get_full_path())

        return render(request, 'admin/top_up_action.html', context={'users': queryset})

    top_up_selected_users.short_description = "Top up selected users' wallets"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('top-up-action/', self.admin_site.admin_view(self.top_up_selected_users)),
        ]
        return custom_urls + urls



admin.site.register(TopUpTransaction)
admin.site.register(PurchaseTransaction)



@admin.register(ExamPin)
class ExamPinAdmin(admin.ModelAdmin):
    list_display = ('name_display', 'price_display', 'is_used')
    list_filter = ('is_used',)
    search_fields = ('pin', 'serial')

    def name_display(self, obj):
        return obj.get_name_display()
    name_display.short_description = 'Card Name'

    def price_display(self, obj):
        pin_price_map = {
            'waec_card': 3500,
            'neco_token': 1150,
            'nabteb_card': 820,
            'waec_verification': 3350,
            'nbais_card': 1280,
            'waec_gce': 28600,
            'neco_verification': 5850,
            'examinify_token': 190,
        }
        return f"₦{pin_price_map.get(obj.name, 'N/A')}"
    price_display.short_description = 'Price'



