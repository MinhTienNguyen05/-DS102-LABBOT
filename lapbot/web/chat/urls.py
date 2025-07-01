from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path("", views.index, name="index"), # URL cho trang chat chính
    path('send_message/', views.send_message, name='send_message'), # URL để xử lý việc gửi tin nhắn từ client (sử dụng AJAX),
    path('intent_detect/', views.intent_detect, name='intent_detect'),
    path('user_message_html/', views.user_message_html, name='user_message_html'),
    path('ai_message_html/', views.ai_message_html, name='ai_message_html'),
    path('delete_all_message/', views.delete_all_message, name='delete_all_message'),
    path('predict_price/', views.predict_price, name='predict_price')
]