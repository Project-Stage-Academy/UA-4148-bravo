from django.urls import path
from investments.views import SubscriptionCreateView

urlpatterns = [
    path("api/v1/investments/subscriptions/create/", SubscriptionCreateView.as_view(), name="subscription-create"),
]