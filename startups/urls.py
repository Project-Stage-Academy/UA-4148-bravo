from django.urls import path
from rest_framework.routers import DefaultRouter
from startups.views import StartupSearchViewSet

router = DefaultRouter()
router.register(r'search', StartupSearchViewSet, basename='startups-search')

urlpatterns = router.urls
