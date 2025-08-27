from django.urls import path
from rest_framework.routers import DefaultRouter
from startups.views.startup import StartupViewSet
from startups.views.startup_elasticsearch import StartupDocumentView
from startups.views.startup_preferences import StartupPreferencesView
from startups.views.bind_company import BindCompanyView

router = DefaultRouter()
router.register(r'startups', StartupViewSet, basename='startup')
router.register(r'startups/search', StartupDocumentView, basename='startups-search')

urlpatterns = router.urls + [
    path('startup/preferences/', StartupPreferencesView.as_view(), name='startup-preferences'),
    path('company/bind/', BindCompanyView.as_view(), name='bind-company'),
]


