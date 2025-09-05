from django.utils import timezone
import logging
from django.db import IntegrityError
from rest_framework import viewsets, status, generics, pagination
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from investors.models import Investor, SavedStartup, FollowedProject
from investors.permissions import IsSavedStartupOwner, IsFollowedProjectOwner
from investors.serializers.investor import InvestorSerializer, SavedStartupSerializer, ViewedStartupSerializer, FollowedProjectSerializer
from investors.serializers.investor_create import InvestorCreateSerializer
from django.shortcuts import get_object_or_404
from .models import ViewedStartup
from startups.models import Startup
from projects.models import Project
from users.cookie_jwt import CookieJWTAuthentication
from users.permissions import IsInvestor, CanCreateCompanyPermission, IsAuthenticatedOr401, IsAuthenticatedInvestor403
from startups.models import Startup
from users.views.base_protected_view import CookieJWTProtectedView
from communications.services import NotificationService

logger = logging.getLogger(__name__)


class InvestorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Investor instances.
    Optimized with select_related to avoid N+1 queries when fetching related user, industry, and location.
    """
    queryset = Investor.objects.select_related("user", "industry", "location")
    serializer_class = InvestorSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes_by_action = {
        "create": [IsAuthenticatedOr401, CanCreateCompanyPermission],
        "default": [IsAuthenticatedOr401],
    }

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        perms = self.permission_classes_by_action.get(self.action, self.permission_classes_by_action["default"])
        return [perm() for perm in perms]

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the request action.
        """
        if self.action == 'create':
            return InvestorCreateSerializer
        return InvestorSerializer


class SavedStartupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing SavedStartup instances.
    Only authenticated investors who own the SavedStartup can modify/delete it.
    """
    permission_classes = [IsAuthenticatedInvestor403]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = SavedStartupSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, "investor"):
            logger.warning(
                "SavedStartup list denied for non-investor",
                extra={"by_user": getattr(user, "pk", None)},
            )
            raise PermissionDenied("Only investors can list saved startups.")
        return SavedStartup.objects.filter(investor=self.request.user.investor)

    def create(self, request, *args, **kwargs):
        user = request.user

        if not hasattr(user, "investor"):
            logger.warning(
                "SavedStartup create denied for non-investor",
                extra={"by_user": getattr(user, "pk", None)},
            )
            raise ValidationError({"non_field_errors": ["Only investors can save startups."]})

        payload = request.data or {}

        if "startup" not in payload or payload.get("startup") in (None, "", []):
            logger.warning(
                "SavedStartup create failed: missing startup",
                extra={"by_user": user.pk},
            )

        status_val = payload.get("status")
        if status_val is not None:
            status_field = SavedStartup._meta.get_field("status")
            valid_status = {c[0] for c in status_field.choices}
            if status_val not in valid_status:
                logger.warning(
                    "SavedStartup create failed: invalid status",
                    extra={"status": status_val, "by_user": user.pk},
                )

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
        except ValidationError as e:
            if startup_id and SavedStartup.objects.filter(
                    investor=user.investor, startup_id=startup_id
            ).exists():
                logger.warning(
                    "SavedStartup create failed: duplicate",
                    extra={"investor_id": user.investor.pk, "startup_id": startup_id, "by_user": user.pk},
                )
            detail = getattr(e, "detail", {})
            if isinstance(detail, dict):
                msgs = detail.get("startup")
                if msgs:
                    if not isinstance(msgs, (list, tuple)):
                        msgs = [msgs]
                    if any("own startup" in str(m).lower() for m in msgs):
                        logger.warning(
                            "SavedStartup create failed: own startup",
                            extra={"startup_id": startup_id, "by_user": getattr(user, "pk", None)},
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


class FollowedProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing FollowedProject instances.
    Only authenticated investors who own the FollowedProject can modify/delete it.
    """
    permission_classes = [IsAuthenticatedInvestor403]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = FollowedProjectSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'investor') and user.investor:
            return FollowedProject.objects.filter(investor=user.investor)
        return FollowedProject.objects.none()

    def create(self, request, *args, **kwargs):
        user = request.user
        payload = request.data

        if "project" not in payload or payload.get("project") in (None, "", []):
            logger.warning(
                "FollowedProject create failed: missing project",
                extra={"by_user": user.pk},
            )
            return Response(
                {"project": ["This field is required."]}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        project_id = payload.get("project")
        if project_id and FollowedProject.objects.filter(
                investor=user.investor, project_id=project_id
        ).exists():
            logger.warning(
                "FollowedProject create failed: duplicate",
                extra={"investor_id": user.investor.pk, "project_id": project_id, "by_user": user.pk},
            )
            existing = FollowedProject.objects.get(investor=user.investor, project_id=project_id)
            return Response(
                FollowedProjectSerializer(existing).data,
                status=status.HTTP_200_OK
            )

        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            if project_id and FollowedProject.objects.filter(
                    investor=user.investor, project_id=project_id
            ).exists():
                logger.warning(
                    "FollowedProject create failed: duplicate",
                    extra={"investor_id": user.investor.pk, "project_id": project_id, "by_user": user.pk},
                )
                existing = FollowedProject.objects.get(investor=user.investor, project_id=project_id)
                return Response(
                    FollowedProjectSerializer(existing).data,
                    status=status.HTTP_200_OK
                )
            detail = getattr(e, "detail", {})
            if isinstance(detail, dict):
                for field, msgs in detail.items():
                    if isinstance(msgs, list):
                        msgs = [msgs]
                    if any("own project" in str(m).lower() for m in msgs):
                        logger.warning(
                            "FollowedProject create failed: own project",
                            extra={"project_id": project_id, "by_user": getattr(user, "pk", None)},
                        )
            raise

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        user = self.request.user
        project = serializer.validated_data.get("project")
        if project is None:
            logger.warning("FollowedProject create failed: missing project", extra={"by_user": user.pk})
            raise ValidationError({"project": "This field is required."})

        startup_user_id = getattr(getattr(project, "startup", None), "user_id", None)
        if startup_user_id == user.pk:
            logger.warning(
                "FollowedProject create failed: own project",
                extra={"project_id": getattr(project, "pk", None), "startup_user_id": startup_user_id, "by_user": user.pk},
            )
            raise ValidationError({"project": "You cannot follow your own project."})

        try:
            instance = serializer.save(investor=user.investor)
        except IntegrityError:
            logger.warning(
                "FollowedProject create failed: duplicate",
                extra={"investor_id": user.investor.pk, "project_id": project.pk, "by_user": user.pk},
            )
            raise ValidationError({"non_field_errors": ["Already followed."]})

        logger.info(
            "FollowedProject created",
            extra={
                "investor_id": user.investor.pk,
                "project_id": project.pk,
                "followed_id": instance.pk,
                "by_user": user.pk,
            },
        )

        try:
            NotificationService.create_project_followed_notification(
                project=project,
                investor_user=user
            )
        except Exception as e:
            logger.warning(f"Failed to create follow notification: {str(e)}")

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()
        data.pop("investor", None)
        data.pop("project", None)

        serializer = self.get_serializer(instance, data=data, partial=True)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            logger.warning(
                "FollowedProject update validation error",
                extra={"followed_id": instance.pk, "by_user": request.user.pk, "errors": getattr(e, "detail", str(e))},
            )
            raise
        self.perform_update(serializer)

        logger.info(
            "FollowedProject updated",
            extra={"followed_id": serializer.instance.pk, "by_user": request.user.pk},
        )
        return Response(serializer.data)

    def perform_destroy(self, instance):
        logger.info(
            "FollowedProject deleted",
            extra={"followed_id": instance.pk, "by_user": self.request.user.pk},
        )
        super().perform_destroy(instance)


class ViewedStartupPagination(pagination.PageNumberPagination):
    """
    Pagination class for recently viewed startups.
    Default page size is 10, can be overridden via ?page_size query parameter.
    """
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class ViewedStartupListView(generics.ListAPIView):
    """
    GET /api/v1/startups/viewed/
    Retrieve a paginated list of recently viewed startups for the authenticated investor.
    """
    serializer_class = ViewedStartupSerializer
    permission_classes = [IsAuthenticatedInvestor403]
    pagination_class = ViewedStartupPagination

    def get_queryset(self):
        return ViewedStartup.objects.filter(investor=self.request.user.investor).select_related('startup').order_by("-viewed_at")


class ViewedStartupCreateView(APIView):
    """
    POST /api/v1/startups/view/{startup_id}/
    Log that the authenticated investor has viewed a specific startup.
    Return the serialized ViewedStartup instance.
    """
    permission_classes = [IsAuthenticatedInvestor403]

    def post(self, request, startup_id):
        startup = get_object_or_404(Startup, id=startup_id)
        investor = request.user.investor 

        viewed_obj, created = ViewedStartup.objects.update_or_create(
            investor=investor,
            startup=startup,
            defaults={"viewed_at": timezone.now()}
        )

        serializer = ViewedStartupSerializer(viewed_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ViewedStartupClearView(APIView):
    """
    DELETE /api/v1/startups/viewed/clear/
    Clear the authenticated investor's viewed startups history.
    Return number of deleted entries.
    """
    permission_classes = [IsAuthenticatedInvestor403]

    def delete(self, request):
        investor = request.user.investor
        deleted_count = investor.viewed_startups.count()
        investor.viewed_startups.clear()
        return Response(
            {"detail": "Viewed startups history cleared successfully.", "deleted_count": deleted_count},
            status=status.HTTP_200_OK
        )


class FollowProjectView(APIView):
    """
    POST /api/v1/projects/follow/{project_id}/
    Allow an investor to follow a project.
    Returns 201 if newly created, 200 if already followed.
    """
    permission_classes = [IsAuthenticatedInvestor403]

    def post(self, request, project_id: int):
        """
        Allow an investor to follow a project.
        Returns 201 if newly created, 200 if already followed.
        """
        project = get_object_or_404(Project, pk=project_id)

        existing_follow = FollowedProject.objects.filter(
            investor=request.user.investor, 
            project=project
        ).first()
        
        if existing_follow:
            return Response(
                FollowedProjectSerializer(existing_follow).data, 
                status=status.HTTP_200_OK
            )

        serializer = FollowedProjectSerializer(
            data={"project": project.id},
            context={"request": request},
        )
        
        try:
            serializer.is_valid(raise_exception=True)
            obj = serializer.save()
            
            try:
                NotificationService.create_project_followed_notification(
                    project=project,
                    investor_user=request.user
                )
            except Exception as e:
                logger.warning(f"Failed to create notification for project follow: {e}")
            
            return Response(FollowedProjectSerializer(obj).data, status=status.HTTP_201_CREATED)
            
        except IntegrityError:
            existing_follow = FollowedProject.objects.get(
                investor=request.user.investor, 
                project=project
            )
            return Response(
                FollowedProjectSerializer(existing_follow).data, 
                status=status.HTTP_200_OK
            )
        except Exception as exc:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            if isinstance(exc, DRFValidationError) and "Already followed." in str(exc.detail):
                obj = FollowedProject.objects.get(investor=request.user.investor, project=project)
                return Response(FollowedProjectSerializer(obj).data, status=status.HTTP_200_OK)
            raise


class SaveStartupView(CookieJWTProtectedView):

    def post(self, request, startup_id: int):
        """
        Allow an investor to save/follow a startup.
        Returns 201 if newly created, 200 if already saved.
        """
        startup = get_object_or_404(Startup, pk=startup_id)

        existing_save = SavedStartup.objects.filter(
            investor=request.user.investor, 
            startup=startup
        ).first()
        
        if existing_save:
            return Response(
                SavedStartupSerializer(existing_save).data, 
                status=status.HTTP_200_OK
            )

        serializer = SavedStartupSerializer(
            data={"startup": startup.id},
            context={"request": request},
        )
        
        try:
            serializer.is_valid(raise_exception=True)
            obj = serializer.save()
            return Response(SavedStartupSerializer(obj).data, status=status.HTTP_201_CREATED)
            
        except IntegrityError:
            existing_save = SavedStartup.objects.get(
                investor=request.user.investor, 
                startup=startup
            )
            return Response(
                SavedStartupSerializer(existing_save).data, 
                status=status.HTTP_200_OK
            )
        except Exception as exc:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            if isinstance(exc, DRFValidationError) and "Already saved." in str(exc.detail):
                obj = SavedStartup.objects.get(investor=request.user.investor, startup=startup)
                return Response(SavedStartupSerializer(obj).data, status=status.HTTP_200_OK)
            raise


class UnfollowProjectView(APIView):
    """
    DELETE /api/v1/projects/unfollow/{project_id}/
    Allow an investor to unfollow a project.
    Returns 204 if successfully unfollowed, 404 if not following.
    """
    permission_classes = [IsAuthenticatedInvestor403]

    def delete(self, request, project_id: int):
        """
        Allow an investor to unfollow a project.
        Returns 204 if successfully unfollowed, 404 if not following.
        """
        project = get_object_or_404(Project, pk=project_id)
        
        try:
            followed_project = FollowedProject.objects.get(
                investor=request.user.investor, 
                project=project
            )
            followed_project.delete()
            
            logger.info(
                "Project unfollowed",
                extra={
                    "investor_id": request.user.investor.pk,
                    "project_id": project.pk,
                    "by_user": request.user.pk,
                },
            )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except FollowedProject.DoesNotExist:
            return Response(
                {"detail": "Project not followed"}, 
                status=status.HTTP_404_NOT_FOUND
            )
