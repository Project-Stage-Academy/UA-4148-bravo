import logging
from django.db import IntegrityError
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from investors.models import Investor, SavedStartup
from investors.serializers import InvestorSerializer, SavedStartupSerializer

logger = logging.getLogger(__name__)


class InvestorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Investor instances.
    Optimized with select_related to avoid N+1 queries when fetching related user, industry, and location.
    """
    queryset = Investor.objects.select_related("user", "industry", "location")
    serializer_class = InvestorSerializer
    permission_classes = [IsAuthenticated]


class IsSavedStartupOwner(BasePermission):
    """
    Custom permission to allow only the owner of a SavedStartup (its investor) to modify or delete it.
    """
    def has_object_permission(self, request, view, obj):
        return hasattr(request.user, "investor") and obj.investor_id == request.user.investor.pk


class SavedStartupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing SavedStartup instances.
    Only authenticated investors who own the SavedStartup can modify/delete it.
    """
    permission_classes = [IsAuthenticated, IsSavedStartupOwner]
    serializer_class = SavedStartupSerializer

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, "investor"):
            logger.warning(
                "SavedStartup list denied for non-investor",
                extra={"by_user": getattr(user, "pk", None)},
            )
            raise PermissionDenied("Only investors can list saved startups.")
        return (
            SavedStartup.objects
            .select_related("startup", "investor")
            .filter(investor=user.investor)
            .order_by("-saved_at")
        )

    def create(self, request, *args, **kwargs):
        user = request.user
        if not hasattr(user, "investor"):
            logger.warning(
                "SavedStartup create denied for non-investor",
                extra={"by_user": getattr(user, "pk", None)},
            )
            raise ValidationError({"non_field_errors": ["Only investors can save startups."]})

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        user = self.request.user
        startup = serializer.validated_data.get("startup")
        if startup.user_id == user.pk:
            logger.warning(
                "SavedStartup create failed: own startup",
                extra={"startup_id": startup.pk, "by_user": user.pk},
            )
            raise ValidationError({"startup": "You cannot save your own startup."})

        try:
            instance = serializer.save(investor=user.investor)
        except IntegrityError:
            logger.warning(
                "SavedStartup create failed: duplicate",
                extra={"investor_id": user.investor.pk, "startup_id": startup.pk, "by_user": user.pk},
            )
            raise ValidationError({"non_field_errors": ["Already saved."]})

        logger.info(
            "SavedStartup created",
            extra={"investor_id": user.investor.pk, "startup_id": startup.pk, "saved_id": instance.pk, "by_user": user.pk},
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        data.pop("investor", None)
        data.pop("startup", None)
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        logger.info(
            "SavedStartup updated",
            extra={"saved_id": serializer.instance.pk, "by_user": request.user.pk},
        )
        return Response(serializer.data)

    def perform_destroy(self, instance):
        logger.info(
            "SavedStartup deleted",
            extra={"saved_id": instance.pk, "by_user": self.request.user.pk},
        )
        super().perform_destroy(instance)

