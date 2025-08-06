from django.urls import path, include
from rest_framework.routers import DefaultRouter
from projects.views import ProjectViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')

urlpatterns = [
    path('', include(router.urls)),
]

# To activate these routes, include this file in your main urls.py (e.g., config/urls.py):
# path('api/', include('projects.urls'))
