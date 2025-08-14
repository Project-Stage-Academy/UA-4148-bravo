from django.urls import path, include
from rest_framework.routers import DefaultRouter
from projects.views import ProjectDocumentView, ProjectViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'projects-documents', ProjectDocumentView, basename='project-document')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
