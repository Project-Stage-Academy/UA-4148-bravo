"""
URL configuration for core project.

Routes are organized by app and follow RESTful naming conventions.
All API endpoints use plural nouns for consistency.
For more information, see:
https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # User authentication endpoints
    path('api/users/', include('users.urls')),        # User management

    # Project-related endpoints
    path('api/projects/', include('projects.urls')),  # Project-related endpoints

    # Profile-related endpoints
    path('api/profiles/', include('profiles.urls')),  # Profile management
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


