from django.urls import path, include
from rest_framework_simplejwt.views import TokenBlacklistView
from .views import CustomTokenObtainPairView

urlpatterns = [
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
]
