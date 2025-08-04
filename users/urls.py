from django.urls import path, include
from rest_framework_simplejwt.views import TokenBlacklistView

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),

    # JWT Logout - See README documentation for request format
    path('auth/jwt/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),
]
