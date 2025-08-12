from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ProjectDocumentView
from investments.views import SubscriptionCreateView

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'projects-documents', ProjectDocumentView, basename='projectdocument')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', ProjectDocumentView.as_view({'get': 'list'}), name='project-search'),
    path('subscriptions/create/', SubscriptionCreateView.as_view(), name='subscription-create'),
]

