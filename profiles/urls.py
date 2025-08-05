from django.urls import path, include
from rest_framework.routers import DefaultRouter
from profiles.views import StartupViewSet, InvestorViewSet

router = DefaultRouter()
router.register(r'startups', StartupViewSet, basename='startup')
router.register(r'investors', InvestorViewSet, basename='investor')

urlpatterns = [
    path('', include(router.urls)),
]
