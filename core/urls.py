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
from users.views import CustomTokenObtainPairView, UserRegistrationView, VerifyEmailView

# API endpoints grouped by app
api_urlpatterns = [
     # User authentication endpoints
    path('users/', include('users.urls')),

    # API endpoints
    #
    # Register
    # URL: /api/v1/auth/register/
    # Req: { email, first_name, last_name, password, password2 }
    # Res: 201 { status, message, user_id, email }
    #
    # Me
    # URL: /api/v1/auth/me/
    # Req: {}
    # Res: 200 { id, email, role, ... }
    #
    # Password reset
    # URL: /api/v1/auth/password/reset/
    # Req: { email }
    # Res: 200
    #
    # Password reset confirm
    # URL: /api/v1/auth/password/reset/confirm/
    # Req: { uid, token, new_password }
    # Res: 200

    path('auth/register/', UserRegistrationView.as_view(), name='user_register'),
    path('auth/me/', CustomTokenObtainPairView.as_view(), name='custom_login'),
    #path('auth/password/reset/', , name='password_reset'),
    #path('auth/password/reset/confirm/', , name='password_reset_confirm'),

    # Djoser authentication endpoints
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),

    # Custom JWT endpoints
    #
    # Create
    # URL: /api/v1/auth/jwt/create/
    # Req: { email, password }
    # Res: 200 { access, refresh }
    #
    # Refresh
    # URL: /api/v1/auth/jwt/refresh/
    # Req: { refresh }
    # Res: 200 { access }
    #
    # Blacklist
    # URL: /api/v1/auth/password/reset/
    # Req: { refresh }
    # Res: 205

    path('auth/jwt/create/', CustomTokenObtainPairView.as_view(), name='jwt-create'),
    path('auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),
    #path('auth/jwt/blacklist/', , name='jwt-blacklist'),

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
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
