from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# from common.notifications import send_notification
from startups.models import Startup
from startups.permissions import IsStartupOwnerOrReadOnly
from startups.serializers.startup_full import StartupSerializer
from startups.serializers.startup_create import StartupCreateSerializer



class StartupViewSet(viewsets.ModelViewSet):
    """
    API viewset for managing Startups.
    Supports filtering, searching, and creation.
    """
    queryset = Startup.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["stage", "industry"]
    search_fields = ["company_name", "description"]

    def get_permissions(self):
        """
        Assign permissions based on action.
        - 'create': IsAuthenticated
        - others: IsAuthenticated + IsStartupOwnerOrReadOnly
        """
        if self.action == "create":
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsStartupOwnerOrReadOnly]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """
        Return serializer class depending on action.
        - 'create': StartupCreateSerializer
        - others: StartupSerializer
        """
        if self.action == "create":
            return StartupCreateSerializer
        return StartupSerializer

    def perform_create(self, serializer):
        """
        Save the startup instance and attach the current user.
        """
        startup = serializer.save(user=self.request.user)
        # Uncomment to send notification when module is ready
        # send_notification(
        #     "startup_created",
        #     f"Startup {startup.company_name} was created by {self.request.user.email}",
        # )


