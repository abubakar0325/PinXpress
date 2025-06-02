from django.urls import path
from . import views

app_name = 'pastquestions'

urlpatterns = [
    path('', views.question_list, name='question_list'),
    path('<int:pk>/', views.question_detail, name='question_detail'),
    path('buy/<int:question_id>/', views.buy_past_question, name='buy_question'),
    path('my-purchases/', views.my_purchases, name='purchase_history'),
    path('initiate-payment/<int:question_id>/', views.initiate_payment, name='initiate_payment'),
    path('download/<int:question_id>/', views.download_question_file, name='download_question_file'),
    path('secure-download/<str:token>/', views.secure_download, name='secure_download'),  # ✅ Added this
]
