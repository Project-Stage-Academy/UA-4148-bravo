from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import StartupDocumentView, StartupViewSet, StartupDetailView

router = DefaultRouter()
# Elasticsearch search endpoints
router.register(r'search', StartupDocumentView, basename='startups-search')

# DB-backed restful endpoints
router.register(r'profiles', StartupViewSet, basename='startups')

urlpatterns = router.urls + [
    # Custom detail view (optional if StartupViewSet already supports retrieve)
    path('profiles/<int:pk>/detail/', StartupDetailView.as_view(), name='startup-detail'),
]
