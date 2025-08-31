from rest_framework.routers import DefaultRouter
from django.urls import path

from startups.views.startup import StartupViewSet
from startups.views.startup_elasticsearch import StartupDocumentView

router = DefaultRouter()
router.register(r'', StartupViewSet, basename='startups')
router.register(r'search', StartupDocumentView, basename='startups-search')

# Get the router's URL patterns
urlpatterns = router.urls

# Add explicit URL patterns for the notification preferences endpoints
startup_viewset = StartupViewSet.as_view({
    'get': 'preferences',
})

startup_preferences_update = StartupViewSet.as_view({
    'patch': 'preferences',
})

startup_email_preferences_get = StartupViewSet.as_view({
    'get': 'get_email_preferences',
})

startup_email_preferences_update = StartupViewSet.as_view({
    'patch': 'update_email_preferences',
})

# Add these URL patterns to the urlpatterns list
urlpatterns += [
    path('preferences/', startup_viewset, name='preferences'),
    path('preferences/update/', startup_preferences_update, name='preferences-update'),
    path('preferences/email/', startup_email_preferences_get, name='email-preferences-get'),
    path('preferences/email/update/', startup_email_preferences_update, name='email-preferences-update'),
]