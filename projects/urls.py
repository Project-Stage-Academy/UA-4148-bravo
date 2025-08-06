from django.urls import path, include
from .views import ProjectDocumentView

urlpatterns = [
  path('api/', include('users.urls')),
  path('search/', ProjectDocumentView.as_view({'get': 'list'}), name='project-search'),
]