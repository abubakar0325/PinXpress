from django.urls import path
from . import views

app_name = 'monnify'
urlpatterns = [
    path('virtual-account/', views.create_virtual_account, name='virtual_account'),
    path("monnify/webhook/", views.monnify_webhook, name="monnify_webhook"),

]
