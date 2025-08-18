"""
URL configuration for core project.

- Routes are organized by app and follow RESTful naming conventions.
- All API endpoints use plural nouns for consistency.
- Versioning is applied via 'api/v1/' to support future evolution.
- JWT authentication and OAuth endpoints are included.
- API schema and docs are available via drf-spectacular.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .healthcheck import elasticsearch_healthcheck
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# JWT and custom authentication views
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    VerifyEmailView,
    TokenBlacklistView,
    OAuthTokenObtainPairView,
    ResendEmailView,
)

# Grouped API endpoints under versioned path
api_urlpatterns = [
    # User endpoints
    path('users/', include('users.urls')),

    # Authentication endpoints
    path('auth/register/', UserRegistrationView.as_view(), name='user_register'),
    path('auth/jwt/create/', CustomTokenObtainPairView.as_view(), name='jwt-create'),
    path('auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),
    path('auth/jwt/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('auth/verify-email/<int:user_id>/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('auth/resend-email/', ResendEmailView.as_view(), name='resend-email'),

    # Custom OAuth endpoint
    path('oauth/login/', OAuthTokenObtainPairView.as_view(), name="oauth_login"),

    # App-specific endpoints
    path('projects/', include('projects.urls')),
    path('startups/', include('startups.urls')),
    path('investors/', include('investors.urls')),
    path('communications/', include('communications.urls')),
    path('chat/', include('chat.urls')),

    # OAuth endpoints (django-allauth)
    path('accounts/', include('allauth.urls')),
]

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),

    # Versioned API entrypoint
    path('api/v1/', include(api_urlpatterns)),

    # API schema and docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Healthcheck endpoint
    path('health/elasticsearch/', elasticsearch_healthcheck),
]

# Serve static and media files only during local development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

