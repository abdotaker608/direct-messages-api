from django.urls import path
from . import views

app_name = 'websocket'

urlpatterns = [
    path('chats', views.ChatsView.as_view(), name='chats'),
    path('<int:pk>/messages', views.MessageView.as_view(), name='messages')
]