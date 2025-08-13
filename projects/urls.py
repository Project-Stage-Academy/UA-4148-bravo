from django.urls import path, include
from rest_framework.routers import DefaultRouter
from projects.views import ProjectViewSet, ProjectDocumentView

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'projects-documents', ProjectDocumentView, basename='projectdocument')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]

