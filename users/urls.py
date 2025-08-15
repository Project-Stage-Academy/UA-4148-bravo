from django.urls import path, include
from rest_framework_simplejwt.views import TokenBlacklistView
from .views import CustomTokenObtainPairView
from .views import CustomPasswordResetView, CustomPasswordResetConfirmView

urlpatterns = [

]
