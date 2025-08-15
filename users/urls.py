from django.urls import path, include
from rest_framework_simplejwt.views import TokenBlacklistView
from .views import CustomTokenObtainPairView
from .views import CustomPasswordResetView, CustomPasswordResetConfirmView
from .views import MeView


urlpatterns = [
    # ----------------------------------------
    # Custom password recovery endpoints
    # ----------------------------------------
    path('reset_password/', CustomPasswordResetView.as_view(), name="custom_reset_password"),
    path('reset_password_confirm/', CustomPasswordResetConfirmView.as_view(), name="custom_reset_password_confirm"),

    # ----------------------------------------
    # Custom authentication endpoint
    # ----------------------------------------
    path('login/', CustomTokenObtainPairView.as_view(), name='custom_login'),

    # ----------------------------------------
    # Djoser authentication endpoints
    # ----------------------------------------
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),

    # ----------------------------------------
    # JWT Logout endpoint
    # ----------------------------------------
    path('auth/jwt/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),

    path("me/", MeView.as_view(), name="auth-me"),
]
