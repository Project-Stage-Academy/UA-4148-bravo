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
from users.views import CustomTokenObtainPairView, UserRegistrationView, VerifyEmailView, CustomPasswordResetView, \
    CustomPasswordResetConfirmView

# API endpoints grouped by app
api_urlpatterns = [
    # User authentication endpoints
    path('users/', include('users.urls')),  # User-specific endpoints

    # Register
    # URL: /api/v1/auth/register/
    # Req: { email, first_name, last_name, password, password2 }
    # Res: 201 { status, message, user_id, email }

    path('auth/register/', UserRegistrationView.as_view(), name='user_register'),

    # Resend register email
    # URL: /api/v1/auth/register/resend/
    # Req: { email, userId }
    # Res: 201 { status, message, user_id, email }

    # path('auth/register/resend', , name='user_register'),

    # Me
    # URL: /api/v1/auth/me/
    # Req: {}
    # Res: 200 { id, email, role, ... }

    # path('auth/me/', CustomTokenObtainPairView.as_view(), name='custom_login'),

    # Password reset
    # URL: /api/v1/auth/password/reset/
    # Req: { email }
    # Res: 200

    path('auth/password/reset/', CustomPasswordResetView.as_view(), name='password_reset'),

    # Password reset confirm
    # URL: /api/v1/auth/password/reset/confirm/
    # Req: { uid, token, new_password }
    # Res: 200

    path('auth/password/reset/confirm/',
         CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),

    # Create
    # URL: /api/v1/auth/jwt/create/
    # Req: { email, password }
    # Res: 200 { access, refresh }

    path('auth/jwt/create/', CustomTokenObtainPairView.as_view(), name='jwt-create'),

    # Refresh
    # URL: /api/v1/auth/jwt/refresh/
    # Req: { refresh }
    # Res: 200 { access }

    path('auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),

    # Blacklist
    # URL: /api/v1/auth/jwt/blacklist/
    # Req: { refresh }
    # Res: 205

    path('auth/jwt/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # Email verification
    path('auth/verify-email/<int:user_id>/<str:token>/',
        VerifyEmailView.as_view(), 
        name='verify-email'),

    # Project-related endpoints
    path('projects/', include('projects.urls')),

    # Startup-related endpoints
    path('startups/', include('startups.urls')),

    # Investor-related endpoints
    path('investors/', include('investors.urls')),

    # OAuth endpoints
    path('accounts/', include('allauth.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_urlpatterns)),  # Versioned API path
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('health/elasticsearch/', elasticsearch_healthcheck),
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
