from rest_framework.routers import DefaultRouter
from investors.views import InvestorViewSet, SavedStartupViewSet

# Register viewsets with the router
router = DefaultRouter()
router.register(r'saved', SavedStartupViewSet, basename='saved-startup')
router.register(r'', InvestorViewSet, basename='investor')

urlpatterns = router.urls
