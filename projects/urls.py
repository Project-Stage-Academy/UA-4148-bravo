from django.urls import path, include
from .views import ProjectSearchViewSet

urlpatterns = [
  path('api/', include('users.urls')),
  path('search/', ProjectSearchViewSet.as_view({'get': 'list'}), name='project-search'),
]