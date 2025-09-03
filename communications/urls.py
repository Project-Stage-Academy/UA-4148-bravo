from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet,
    NotificationTypeViewSet,
    UserNotificationPreferenceViewSet,
    EmailNotificationPreferenceViewSet,
)

router = DefaultRouter()

router.register(
    r'notifications',
    NotificationViewSet,
    basename='notification'
)

router.register(
    r'notification-types',
    NotificationTypeViewSet,
    basename='notification-type'
)

router.register(
    r'preferences',
    UserNotificationPreferenceViewSet,
    basename='user-notification-preference'
)

router.register(
    r'email-preferences',
    EmailNotificationPreferenceViewSet,
    basename='email-notification-preference'
)

app_name = 'communications'

urlpatterns = [
    path('', include(router.urls)),
]