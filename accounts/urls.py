from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('resend-activation/', views.resend_activation_view, name='resend_activation'),
    path('dashboard', views.dashboard_view, name='dashboard'),
    path('buy-exam-pin/', views.buy_exam_pin, name='buy_exam_pin'),
    path('download-pin-pdf/', views.download_pin_pdf, name='download_pin_pdf'),
    path('profile/', views.profile_view, name='profile'),
    path('wallet-top-up/', views.wallet_top_up, name='wallet_top_up'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('password/change/', views.change_password, name='change_password'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
    path('history/', views.all_transaction_history, name='transaction_history'),
    path('run-migrations/', views.run_migrations, name='run_migrations'),
    path('history/pdf/', views.generate_pdf_report, name='transaction_history_pdf'),
]
