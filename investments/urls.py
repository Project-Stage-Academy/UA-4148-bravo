from django.urls import path
from .views import SubscriptionCreateView

urlpatterns = [
    path('subscriptions/create/', SubscriptionCreateView.as_view(), name='subscription-create'),
]