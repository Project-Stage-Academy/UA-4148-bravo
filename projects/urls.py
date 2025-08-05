# your main urls.py (core/urls.py или config/urls.py)
from django.urls import path, include

urlpatterns = [
    path('api/', include('users.urls')),
    path('api/', include('projects.urls')),
]
