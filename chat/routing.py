from django.urls import path
from .consumers import InvestorStartupMessageConsumer, NotificationConsumer

websocket_urlpatterns = [
    path('ws/chat/<str:other_user_email>/', InvestorStartupMessageConsumer.as_asgi()),
    path('ws/notifications/', NotificationConsumer.as_asgi()),
]
