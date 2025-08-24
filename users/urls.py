from django.urls import path
from users.views.auth_views import UserRegistrationView, MeView
from users.views.email_views import VerifyEmailView, ResendEmailView
from users.views.oauth_view import OAuthTokenObtainPairView
from users.views.password_views import CustomPasswordResetView, CustomPasswordResetConfirmView
from users.views.token_views import (
    CustomTokenObtainPairView,
    CookieTokenRefreshView,
    JWTLogoutView,
    CSRFTokenView
)

urlpatterns = [
    # Sign up
    path('register/', UserRegistrationView.as_view(), name='user_register'),

    # For CSRF-cookie
    path('csrf/', CSRFTokenView.as_view(), name='csrf-init'),

    # JWT Auth
    path('jwt/create/', CustomTokenObtainPairView.as_view(), name='jwt-create'),
    path('jwt/refresh/', CookieTokenRefreshView.as_view(), name='jwt-refresh'),
    path('jwt/logout/', JWTLogoutView.as_view(), name='jwt-logout'),

    # Password reset
    path('password/reset/', CustomPasswordResetView.as_view(), name='custom_reset_password'),
    path('password/reset/confirm/', CustomPasswordResetConfirmView.as_view(), name='custom_reset_password_confirm'),

    # Get current user
    path("me/", MeView.as_view(), name="auth-me"),

    # Email verification
    path('verify-email/<int:user_id>/<str:token>/', VerifyEmailView.as_view(), name='verify-email'),

    # Resend verification email
    path('resend-email/', ResendEmailView.as_view(), name='resend-email'),

    # OAuth
    path('oauth/login/', OAuthTokenObtainPairView.as_view(), name='oauth_login'),

]
