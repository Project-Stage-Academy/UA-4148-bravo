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
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView
from users.views import CustomTokenObtainPairView, UserRegistrationView, VerifyEmailView

# API endpoints grouped by app
api_urlpatterns = [
    # User authentication endpoints
    path('users/', include('users.urls')),
    path('register/', UserRegistrationView.as_view(), name='user_register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='custom_login'),

    # Djoser authentication endpoints
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),

    # Custom JWT endpoints
    path('auth/jwt/create/', CustomTokenObtainPairView.as_view(), name='jwt-create'),
    path('auth/jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),

    # Email verification
    path('api/auth/verify-email/<int:user_id>/<str:token>/', 
        VerifyEmailView.as_view(), 
        name='verify-email'),

    # Project-related endpoints
    path('projects/', include('projects.urls')),

    # Profile-related endpoints
    path('profiles/', include('profiles.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_urlpatterns)),  # Versioned API path
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



