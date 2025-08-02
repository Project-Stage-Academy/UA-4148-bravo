from django.urls import path, include
from .views import CustomTokenObtainPairView

urlpatterns = [
    # Djoser endpoints for registration, password reset, etc.
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),

    # Custom JWT login endpoint
    path('login/', CustomTokenObtainPairView.as_view(), name='custom_login'),
]
