from rest_framework.routers import DefaultRouter

from investors.views import InvestorViewSet, SavedStartupViewSet
from startups.views.startup import StartupViewSet


# Register viewsets with the router
router = DefaultRouter()
router.register(r'saved', SavedStartupViewSet, basename='saved-startup')
router.register(r'', InvestorViewSet, basename='investor')

# Include router-generated URLs
#urlpatterns = [
#    path('', include(router.urls)),
#]
urlpatterns = router.urls