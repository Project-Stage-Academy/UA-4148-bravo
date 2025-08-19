from django.urls import path, include
from rest_framework_simplejwt.views import TokenBlacklistView
from .views import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    VerifyEmailView,
    OAuthTokenObtainPairView,
    CustomPasswordResetView,
    CustomPasswordResetConfirmView,
    ResendEmailView,
    MeView,
    JWTRefreshView,
    JWTLogoutView,
)


urlpatterns = [
    # Sign up
    path('register/', UserRegistrationView.as_view(), name='user_register'),

    # JWT Auth
    path('jwt/create/', CustomTokenObtainPairView.as_view(), name='jwt-create'),
    path('jwt/refresh/', JWTRefreshView.as_view(), name='jwt-refresh'),
    path('jwt/logout/', JWTLogoutView.as_view(), name='token_blacklist'),

    # Password reset
    path('password/reset/', CustomPasswordResetView.as_view(), name='custom_reset_password'),
    path('password/reset/confirm/', CustomPasswordResetConfirmView.as_view(), name='custom_reset_password_confirm'),

    # ----------------------------------------
    # JWT Logout endpoint
    # ----------------------------------------
    path('auth/jwt/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # Get current user
    path("me/", MeView.as_view(), name="auth-me"),

    # Email verification
    path('verify-email/<int:user_id>/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),

    # Resend verification email
    path('resend-email/', ResendEmailView.as_view(), name='resend-email'),

    # OAuth
    path('oauth/login/', OAuthTokenObtainPairView.as_view(), name='oauth_login'),

]
