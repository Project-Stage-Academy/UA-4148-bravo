"""
URL configuration for core project.

Routes are organized by app and follow RESTful naming conventions.
All API endpoints use plural nouns for consistency.
Versioning is applied via 'api/v1/' to support future evolution.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from .healthcheck import elasticsearch_healthcheck
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    VerifyEmailView,
    TokenBlacklistView,
)

# Grouped API endpoints under versioned path
api_urlpatterns = [
    # User-specific endpoints
    path('users/', include('users.urls')),

    # Authentication endpoints
    path('auth/register/', UserRegistrationView.as_view(), name='user_register'),
    path('auth/jwt/create/', CustomTokenObtainPairView.as_view(), name='jwt-create'),
    path('auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),
    path('auth/jwt/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('auth/verify-email/<int:user_id>/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),

    # App-specific endpoints
    path('projects/', include('projects.urls')),
    path('startups/', include('startups.urls')),
    path('investors/', include('investors.urls')),

    # OAuth endpoints
    path('accounts/', include('allauth.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_urlpatterns)),  # Only versioned API path is used

    # API schema and docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Healthcheck
    path('health/elasticsearch/', elasticsearch_healthcheck),
    path('accounts/', include('allauth.urls')),
]

# Serve static and media files only during local development.
# In production, use a web server (e.g., Nginx) or object storage (e.g., AWS S3).
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

