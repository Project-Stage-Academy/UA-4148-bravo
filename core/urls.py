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
from users.views import CustomTokenObtainPairView, UserRegistrationView, VerifyEmailView, ResendEmailView

# API endpoints grouped by app
api_urlpatterns = [
     # User authentication endpoints
    path('users/', include('users.urls')),

    # API endpoints
    path('api/register/', UserRegistrationView.as_view(), name='user_register'),
    path('api/login/', CustomTokenObtainPairView.as_view(), name='custom_login'),
    path('auth/resend-email/', ResendEmailView.as_view(), name='resend-email'),

    # Djoser authentication endpoints
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),

    # Custom JWT endpoints
    path('api/auth/jwt/create/', CustomTokenObtainPairView.as_view(), name='jwt-create'),
    path('api/auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),

    # Email verification
    path('api/auth/verify-email/<int:user_id>/<str:token>/', 
        VerifyEmailView.as_view(), 
        name='verify-email'),

    # Project-related endpoints
    path('projects/', include('projects.urls')),

    # Startup-related endpoints
    path('startups/', include('startups.urls')),

    # Investor-related endpoints
    path('investors/', include('investors.urls')),
  
    # OAuth endpoints
    path('api/accounts/', include('allauth.urls')),
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
