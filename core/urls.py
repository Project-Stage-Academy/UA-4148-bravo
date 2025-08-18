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
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from users.views import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    VerifyEmailView,
    OAuthTokenObtainPairView,
    ResendEmailView,
    CustomPasswordResetView,
    CustomPasswordResetConfirmView,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Versioned API
    path('api/v1/users/', include('users.urls')),

    # Authentication & registration
    path('api/v1/auth/register/', UserRegistrationView.as_view(), name='user_register'),
    path('api/v1/auth/jwt/create/', CustomTokenObtainPairView.as_view(), name='jwt-create'),
    path('api/v1/auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),
    path('api/v1/auth/jwt/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('api/v1/auth/verify-email/<int:user_id>/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),
    path('api/v1/auth/resend-email/', ResendEmailView.as_view(), name='resend-email'),
    path('api/v1/oauth/login/', OAuthTokenObtainPairView.as_view(), name="oauth_login"),
    path('api/v1/auth/password/reset/', CustomPasswordResetView.as_view(), name="password-reset"),
    path('api/v1/auth/password/reset/confirm/', CustomPasswordResetConfirmView.as_view(), name="password-reset-confirm"),

    # Domain apps
    path('api/v1/projects/', include('projects.urls')),
    path('api/v1/startups/', include('startups.urls')),
    path('api/v1/investors/', include('investors.urls')),
    path('api/v1/investments/', include('investments.urls')),
    path('api/v1/communications/', include('communications.urls')),

    # Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Health & third-party
    path('health/elasticsearch/', elasticsearch_healthcheck),
    path('accounts/', include('allauth.urls')),
    path("chat/", include("chat.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)