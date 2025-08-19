from django.urls import path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularYAMLAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema-json"),
    path("schema.yaml", SpectacularYAMLAPIView.as_view(), name="schema-yaml"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema-json"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema-json"), name="redoc"),
]
