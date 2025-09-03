"""
URL configuration for core project.

Routes are organized by app and follow RESTful naming conventions.
All API endpoints use plural nouns for consistency.
Versioning is applied via 'api/v1/' to support future evolution.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .healthcheck import elasticsearch_healthcheck

urlpatterns = [
    path('admin/', admin.site.urls),

    # Versioned API
    path('api/v1/auth/', include('users.urls')),
    path('api/v1/projects/', include('projects.urls')),
    path('api/v1/startups/', include('startups.urls')),
    path('api/v1/investors/', include('investors.urls')),
    path('api/v1/investments/', include(('investments.urls', 'investments'), namespace='investments')),
    path('api/v1/communications/', include('communications.urls')),
    path('api/v1/search/', include('search.urls')),

    # Health & allauth
    path('health/elasticsearch/', elasticsearch_healthcheck),

    path("api/v1/chat/", include("chat.urls")),

]

# Interactive API docs (Swagger/ReDoc) and machine-readable OpenAPI schema
if getattr(settings, 'DOCS_ENABLED', True):
    urlpatterns += [path('api/', include('core.urls_docs'))]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
