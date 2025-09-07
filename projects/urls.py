from django.urls import path, include
from rest_framework.routers import DefaultRouter

from investments.views import SubscriptionCreateView
from projects.views import ProjectDocumentView, ProjectViewSet
from investors.views import ProjectFollowCreateView, ProjectFollowersListView

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'projects-documents', ProjectDocumentView, basename='project-document')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', ProjectDocumentView.as_view({'get': 'list'}), name='project-search'),
    path("<int:project_id>/subscribe/", SubscriptionCreateView.as_view(), name="project-subscribe"),
    path("<int:project_id>/follow/", ProjectFollowCreateView.as_view(), name="project-follow"),
    path("<int:project_id>/followers/", ProjectFollowersListView.as_view(), name="project-followers"),
]
