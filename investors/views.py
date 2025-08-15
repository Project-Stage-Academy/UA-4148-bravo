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
    queryset = Investor.objects.select_related("user", "industry", "location")
    serializer_class = InvestorSerializer
    permission_classes = [IsAuthenticated]


class IsSavedStartupOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, "investor"):
            return False
        return obj.investor_id == request.user.investor.pk


class SavedStartupViewSet(viewsets.ModelViewSet):
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

        payload = request.data or {}

        # 1) Missing startup -> expected WARN for tests
        if "startup" not in payload or payload.get("startup") in (None, "", []):
            logger.warning(
                "SavedStartup create failed: missing startup",
                extra={"by_user": user.pk},
            )

        # 2) Invalid status -> expected WARN for tests
        status_val = payload.get("status")
        if status_val is not None:
            status_field = SavedStartup._meta.get_field("status")
            valid_status = {c[0] for c in status_field.choices}
            if status_val not in valid_status:
                logger.warning(
                    "SavedStartup create failed: invalid status",
                    extra={"status": status_val, "by_user": user.pk},
                )

        # 3) Duplicate pre-check -> WARN before serializer validation
        startup_id = payload.get("startup")
        if startup_id and SavedStartup.objects.filter(
            investor=user.investor, startup_id=startup_id
        ).exists():
            logger.warning(
                "SavedStartup create failed: duplicate",
                extra={"investor_id": user.investor.pk, "startup_id": startup_id, "by_user": user.pk},
            )

        serializer = self.get_serializer(data=payload)

        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            # If UniqueTogetherValidator caught duplicate, log it here too
            if startup_id and SavedStartup.objects.filter(
                investor=user.investor, startup_id=startup_id
            ).exists():
                logger.warning(
                    "SavedStartup create failed: duplicate",
                    extra={"investor_id": user.investor.pk, "startup_id": startup_id, "by_user": user.pk},
                )
            raise

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "investor"):
            logger.warning(
                "SavedStartup create denied for non-investor",
                extra={"by_user": getattr(user, "pk", None)},
            )
            raise ValidationError({"non_field_errors": ["Only investors can save startups."]})

        startup = serializer.validated_data.get("startup")
        if startup is None:
            logger.warning("SavedStartup create failed: missing startup", extra={"by_user": user.pk})
            raise ValidationError({"startup": "This field is required."})

        status_field = SavedStartup._meta.get_field("status")
        valid_status = {choice[0] for choice in status_field.choices}
        status_val = serializer.validated_data.get("status")
        if status_val and status_val not in valid_status:
            logger.warning(
                "SavedStartup create failed: invalid status",
                extra={"status": status_val, "by_user": user.pk},
            )
            raise ValidationError({"status": f"Invalid status '{status_val}'."})

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
            extra={
                "investor_id": user.investor.pk,
                "startup_id": startup.pk,
                "saved_id": instance.pk,
                "by_user": user.pk,
            },
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        data.pop("investor", None)
        data.pop("startup", None)

        serializer = self.get_serializer(instance, data=data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            logger.warning(
                "SavedStartup update validation error",
                extra={"saved_id": instance.pk, "by_user": request.user.pk, "errors": getattr(e, "detail", str(e))},
            )
            raise
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
