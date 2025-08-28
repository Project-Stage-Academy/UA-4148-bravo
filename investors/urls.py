from rest_framework.routers import DefaultRouter
from investors.views import InvestorViewSet, SavedStartupViewSet
from startups.views.startup import StartupViewSet

from django.urls import path
from .views import (
    ViewedStartupListView,
    ViewedStartupCreateView,
    ViewedStartupClearView
)

# Register viewsets with the router
router = DefaultRouter()
router.register(r'saved', SavedStartupViewSet, basename='saved-startup')
router.register(r'', InvestorViewSet, basename='investor')

urlpatterns = [
    # Endpoint 1: GET recently viewed startups
    path('startups/viewed/', ViewedStartupListView.as_view(), name='viewed-startups-list'),

    # Endpoint 2: POST log a startup view
    path('startups/view/<uuid:startup_id>/', ViewedStartupCreateView.as_view(), name='viewed-startup-create'),

    # Endpoint 3: DELETE clear viewed startups history
    path('startups/viewed/clear/', ViewedStartupClearView.as_view(), name='viewed-startups-clear'),
]
urlpatterns = router.urls
