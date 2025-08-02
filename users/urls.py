from django.urls import path
from .views import CustomTokenObtainPairView

urlpatterns = [
    # ----------------------------------------
    # Custom authentication endpoint
    # ----------------------------------------
    path('login/', CustomTokenObtainPairView.as_view(), name='custom_login'),
]
