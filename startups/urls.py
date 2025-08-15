from rest_framework.routers import DefaultRouter

from startups.views.startup import StartupViewSet
from startups.views.startup_elasticsearch import StartupDocumentView

router = DefaultRouter()
router.register(r'', StartupViewSet, basename='startup')
router.register(r'search', StartupDocumentView, basename='startups-search')

urlpatterns = router.urls