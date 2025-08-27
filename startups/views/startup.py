from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.notifications import send_notification
from users.models import UserPreference
from .models import Startup
from .permissions import IsStartupUser, CanCreateCompanyPermission
from .serializers import StartupSerializer, StartupCreateSerializer


class StartupViewSet(viewsets.ModelViewSet):
    queryset = Startup.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["stage", "industry"]
    search_fields = ["name", "description"]

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [IsAuthenticated, CanCreateCompanyPermission]
        else:
            permission_classes = [IsAuthenticated, IsStartupUser]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "create":
            return StartupCreateSerializer
        return StartupSerializer

    def perform_create(self, serializer):
        startup = serializer.save(user=self.request.user)
        send_notification(
            "startup_created",
            f"Startup {startup.name} was created by {self.request.user.email}",
        )

    def _get_or_create_user_pref(self, request):
        """Helper to get or create user preferences object."""
        return UserPreference.objects.get_or_create(user=request.user)[0]

    @action(detail=False, methods=["get"], url_path="preferences")
    def preferences(self, request):
        """Return user preferences for startups."""
        user_pref = self._get_or_create_user_pref(request)
        return Response({"startup_notifications": user_pref.startup_notifications})

    @action(detail=False, methods=["post"], url_path="preferences/update_type")
    def update_type_preference(self, request):
        """Update user preference for receiving startup notifications."""
        user_pref = self._get_or_create_user_pref(request)
        pref_type = request.data.get("startup_notifications")

        if pref_type not in ["ALL", "MENTIONS_ONLY", "NONE"]:
            return Response(
                {"error": "Invalid preference type."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_pref.startup_notifications = pref_type
        user_pref.save()
        return Response({"startup_notifications": user_pref.startup_notifications})
