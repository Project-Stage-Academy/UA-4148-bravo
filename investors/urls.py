from django.urls import path
from rest_framework.routers import DefaultRouter
from startups.views.startup import StartupViewSet
from .views import (
    ViewedStartupListView,
    ViewedStartupCreateView,
    ViewedStartupClearView,
    InvestorListView,
    InvestorDetailView,
    ProjectFollowCreateView,
    ProjectFollowListView,
    ProjectFollowDetailView,
    ProjectFollowersListView
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
    
    # GET /api/v1/investors/
    path("investors/", InvestorListView.as_view(), name="investor-list"),

    # GET /api/v1/investors/{id}/
    path("investors/<int:pk>/", InvestorDetailView.as_view(), name="investor-detail"),
   
    # GET /api/v1/investors/follows/ - List followed projects
    path("follows/", ProjectFollowListView.as_view(), name="project-follow-list"),
    
    # GET /api/v1/investors/follows/{id}/ - Get follow details
    # PATCH /api/v1/investors/follows/{id}/ - Unfollow project
    path("follows/<int:pk>/", ProjectFollowDetailView.as_view(), name="project-follow-detail"),
] + router.urls

