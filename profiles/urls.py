from django.urls import path, include
from rest_framework.routers import DefaultRouter
from profiles.views import StartupViewSet, InvestorViewSet

# Register viewsets with the router
router = DefaultRouter()
router.register(r'startups', StartupViewSet, basename='startup')
router.register(r'investors', InvestorViewSet, basename='investor')

# Include router-generated URLs
#urlpatterns = [
#    path('', include(router.urls)),
#]
urlpatterns = router.urls