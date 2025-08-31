from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet,
    NotificationTypeViewSet,
    UserNotificationPreferenceViewSet,
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

app_name = 'communications'

urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns += [
    path('preferences/email-preferences/', 
         UserNotificationPreferenceViewSet.as_view({'get': 'get_email_preferences'}), 
         name='user-notification-preference-email-preferences'),
         
    path('preferences/<int:pk>/email-preferences/', 
         UserNotificationPreferenceViewSet.as_view({'patch': 'update_email_preferences'}), 
         name='user-notification-preference-update-email-preferences'),
]