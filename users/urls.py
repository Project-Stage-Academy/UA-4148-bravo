from django.urls import path, include
from .views import CustomPasswordResetView, CustomPasswordResetConfirmView

urlpatterns = [
    # Custom endpoints for password recovery
    path('reset_password/', CustomPasswordResetView.as_view(), name="custom_reset_password"),
    path('reset_password_confirm/', CustomPasswordResetConfirmView.as_view(), name="custom_reset_password_confirm"),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
