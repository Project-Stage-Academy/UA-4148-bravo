# startups/urls.py
from rest_framework.routers import DefaultRouter
from .views import StartupDocumentView, StartupViewSet

router = DefaultRouter()
# Elasticsearch search endpoints (keeps existing naming)
router.register(r'search', StartupDocumentView, basename='startups-search')

# DB-backed restful endpoints for profiles and detail
router.register(r'profiles', StartupViewSet, basename='startups')

urlpatterns = router.urls
