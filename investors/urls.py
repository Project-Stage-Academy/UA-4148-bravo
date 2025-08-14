from rest_framework.routers import DefaultRouter

from investors.views import InvestorViewSet
from startups.views.startup import StartupViewSet

# Register viewsets with the router
router = DefaultRouter()
router.register(r'startups', StartupViewSet, basename='startup')
router.register(r'investors', InvestorViewSet, basename='investor')

# Include router-generated URLs
#urlpatterns = [
#    path('', include(router.urls)),
#]
urlpatterns = router.urls