from django.urls import path
from .views import StartupSearchViewSet

urlpatterns = [
    path('search/', StartupSearchViewSet.as_view({'get': 'list'}), name='startup-search'),
]