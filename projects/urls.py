from django.urls import path, include
from rest_framework.routers import DefaultRouter

from projects.views import ProjectDocumentView, ProjectViewSet
from investments.views import SubscriptionCreateView

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'projects-documents', ProjectDocumentView, basename='project-document')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', ProjectDocumentView.as_view({'get': 'list'}), name='project-search'),
]
