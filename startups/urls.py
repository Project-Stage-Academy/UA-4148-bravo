from rest_framework.routers import DefaultRouter

from startups.views.startup import StartupViewSet
from startups.views.startup_elasticsearch import StartupDocumentView

router = DefaultRouter()
# /api/v1/startups/search/
router.register(r'search', StartupDocumentView, basename='startups-search')
# /api/v1/startups/ , /api/v1/startups/{id}/
router.register(r'', StartupViewSet, basename='startup')
urlpatterns = router.urls