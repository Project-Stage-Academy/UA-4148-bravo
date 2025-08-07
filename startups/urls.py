from django.urls import path
from rest_framework.routers import DefaultRouter
from startups.views import StartupDocumentView

router = DefaultRouter()
router.register(r'search', StartupDocumentView, basename='startups-search')

urlpatterns = router.urls
