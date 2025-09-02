from django.urls import path
from rest_framework.routers import DefaultRouter
from startups.views.startup import StartupViewSet

from django.urls import path
from .views import (
    ViewedStartupListView,
    ViewedStartupCreateView,
    ViewedStartupClearView
)
from investors.views import InvestorViewSet, SavedStartupViewSet, SaveStartupView
from investors.views_saved import InvestorSavedStartupsList, UnsaveStartupView

router = DefaultRouter()
router.register(r'saved', SavedStartupViewSet, basename='saved-startup')
router.register(r'', InvestorViewSet, basename='investor')

urlpatterns = [
    # Endpoint 1: GET recently viewed startups
    path('startups/viewed/', ViewedStartupListView.as_view(), name='viewed-startup-list'),

    # Endpoint 2: POST log a startup view
    path('startups/view/<int:startup_id>/', ViewedStartupCreateView.as_view(), name='viewed-startup-create'),

    # Endpoint 3: DELETE clear viewed startups history
    path('startups/viewed/clear/', ViewedStartupClearView.as_view(), name='viewed-startup-clear'),

    # GET /api/v1/investors/saved-startups/
    path("saved-startups/", InvestorSavedStartupsList.as_view(), name="investor-saved-startups"),

    # POST /api/v1/investors/startups/<startup_id>/save/
    path("startups/<int:startup_id>/save/", SaveStartupView.as_view(), name="startup-save"),

    # DELETE /api/v1/investors/startups/<startup_id>/unsave/
    path("startups/<int:startup_id>/unsave/", UnsaveStartupView.as_view(), name="startup-unsave"),
] + router.urls
