from django.urls import path
from rest_framework.routers import DefaultRouter

from startups.views.startup_elasticsearch import StartupDocumentView
from startups.views.startup import StartupViewSet, StartupDetailView

router = DefaultRouter()

# RESTful endpoints backed by the database
router.register(r'profiles', StartupViewSet, basename='startups')

# Elasticsearch-based search endpoint
router.register(r'search', StartupDocumentView, basename='startups-search')

urlpatterns = router.urls + [
    # Custom detail view (optional if StartupViewSet already supports retrieve)
    path('profiles/<int:pk>/detail/', StartupDetailView.as_view(), name='startup-detail'),
]
