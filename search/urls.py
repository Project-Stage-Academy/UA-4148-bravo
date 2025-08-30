from django.urls import path
from .views import StartupSearchView, ProjectSearchView

urlpatterns = [
    path("startups/", StartupSearchView.as_view(), name="startup-search"),
    path("projects/", ProjectSearchView.as_view(), name="project-search"),
]
