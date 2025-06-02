from django.contrib import admin
from .models import ExamCategory, PastQuestion, PurchaseTransaction

@admin.register(ExamCategory)
class ExamCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(PastQuestion)
class PastQuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'description')

@admin.register(PurchaseTransaction)
class PurchaseTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'payment_reference', 'purchased_at')
    search_fields = ('user__username', 'payment_reference')
    list_filter = ('purchased_at',)
