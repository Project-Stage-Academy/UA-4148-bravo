from django.urls import path
from rest_framework.routers import DefaultRouter
from investors.views import InvestorViewSet, SavedStartupViewSet, SaveStartupView
from investors.views_saved import InvestorSavedStartupsList, UnsaveStartupView

router = DefaultRouter()
router.register(r'saved', SavedStartupViewSet, basename='saved-startup')
router.register(r'', InvestorViewSet, basename='investor')

urlpatterns = [
    # GET /api/v1/investors/saved-startups/
    path("saved-startups/", InvestorSavedStartupsList.as_view(), name="investor-saved-startups"),

    # POST /api/v1/investors/startups/<startup_id>/save/
    path("startups/<int:startup_id>/save/", SaveStartupView.as_view(), name="startup-save"),

    # DELETE /api/v1/investors/startups/<startup_id>/unsave/
    path("startups/<int:startup_id>/unsave/", UnsaveStartupView.as_view(), name="startup-unsave"),
] + router.urls