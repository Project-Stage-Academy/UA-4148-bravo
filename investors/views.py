import logging
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from rest_framework import viewsets, status, generics, pagination, permissions
from rest_framework.exceptions import ParseError, PermissionDenied, ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from users.cookie_jwt import CookieJWTAuthentication
from users.permissions import (
    IsAuthenticatedOr401, CanCreateCompanyPermission, HasActiveCompanyAccount, 
    IsAuthenticatedInvestor403, IsInvestor
)
from rest_framework.permissions import IsAuthenticated
from .permissions import IsSavedStartupOwner
from users.views.base_protected_view import CookieJWTProtectedView
from .models import Investor, ProjectFollow, ViewedStartup, SavedStartup
from .serializers import InvestorSerializer, InvestorCreateSerializer
from .serializers.project_follow import (
    ProjectFollowCreateSerializer,
    ProjectFollowSerializer,
)
from .serializers.investor import SavedStartupSerializer, ViewedStartupSerializer, InvestorListSerializer
from .filters import InvestorFilter
from projects.models import Project
from startups.models import Startup

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
        "create": [IsAuthenticatedOr401, CanCreateCompanyPermission, HasActiveCompanyAccount],
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
    permission_classes = [IsAuthenticatedOr401, IsInvestor, IsSavedStartupOwner, HasActiveCompanyAccount]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = SavedStartupSerializer

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
    permission_classes = [IsAuthenticated, IsInvestor, HasActiveCompanyAccount]
    pagination_class = ViewedStartupPagination

    def get_queryset(self):
        return ViewedStartup.objects.filter(investor=self.request.user.investor).select_related('startup').order_by(
            "-viewed_at")


class ViewedStartupCreateView(APIView):
    """
    POST /api/v1/startups/view/{startup_id}/
    Log that the authenticated investor has viewed a specific startup.
    Return the serialized ViewedStartup instance.
    """
    permission_classes = [IsAuthenticated, IsInvestor]

    def post(self, request, startup_id):
        startup = get_object_or_404(Startup, id=startup_id)
        if not hasattr(request.user, "investor"):
            return Response({"detail": "User is not an investor."}, status=status.HTTP_403_FORBIDDEN)
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
    permission_classes = [IsAuthenticated, IsInvestor, HasActiveCompanyAccount]

    def delete(self, request):
        investor = request.user.investor
        deleted_count = investor.viewed_startups.count()
        investor.viewed_startups.clear()
        return Response(
            {"detail": "Viewed startups history cleared successfully.", "deleted_count": deleted_count},
            status=status.HTTP_200_OK
        )


class SaveStartupView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedOr401, HasActiveCompanyAccount]

    def post(self, request, startup_id: int):
        """
        Allow an investor to save/follow a startup.
        Returns 201 if newly created, 200 if already saved.
        """
        startup = get_object_or_404(Startup, pk=startup_id)

        serializer = SavedStartupSerializer(
            data={"startup": startup.id},
            context={"request": request},
        )
        try:
            serializer.is_valid(raise_exception=True)
            obj = serializer.save()
            return Response(SavedStartupSerializer(obj).data, status=status.HTTP_201_CREATED)
        except Exception as exc:
            from rest_framework.exceptions import ValidationError as DRFValidationError
            if isinstance(exc, DRFValidationError) and "Already saved." in str(exc.detail):
                obj = SavedStartup.objects.get(investor=request.user.investor, startup=startup)
                return Response(SavedStartupSerializer(obj).data, status=status.HTTP_200_OK)
            raise

class InvestorListView(generics.ListAPIView):
    """
    API view to list investors with filtering and strict ordering validation.
    Only authenticated users can access. Invalid ordering fields return 400.
    """
    queryset = Investor.objects.all()
    serializer_class = InvestorListSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_class = InvestorFilter

    def get_queryset(self):
        queryset = Investor.objects.all()
        ordering = self.request.query_params.get("ordering")
        allowed_ordering_fields = [f.name for f in Investor._meta.fields]

        if ordering:
            field_name = ordering.lstrip("-")
            if field_name not in allowed_ordering_fields:
                raise ValidationError({"error": "Invalid ordering field"})
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by("company_name")
        return queryset

class InvestorDetailView(generics.RetrieveAPIView):
    """
    Returns a single investor profile.
    Only authenticated users can access.
    """
    queryset = Investor.objects.all()
    serializer_class = InvestorSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProjectFollowCreateView(CreateAPIView):
    """
    API view for creating project follow relationships.
    
    Allows authenticated investors to follow projects to receive notifications
    about project updates and milestones.
    
    POST /api/v1/projects/{project_id}/follow/
    """
    serializer_class = ProjectFollowCreateSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedInvestor403, HasActiveCompanyAccount]

    def get_serializer_context(self):
        """Add project and request to serializer context."""
        context = super().get_serializer_context()
        project_id = self.kwargs.get('project_id')
        try:
            project = get_object_or_404(Project, id=project_id)
            context['project'] = project
        except (ValueError, Project.DoesNotExist):
            pass
        return context

    def create(self, request, *args, **kwargs):
        """Create a new project follow relationship."""
        project_id = self.kwargs.get('project_id')
        
        try:
            project = get_object_or_404(Project, id=project_id)
        except (ValueError, Project.DoesNotExist):
            return Response(
                {"detail": "Project not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            project_follow = serializer.save()
            
            logger.info(
                f"Project follow created: investor={request.user.investor.id}, project={project.id}",
                extra={
                    "investor_id": request.user.investor.id,
                    "project_id": project.id,
                    "project_follow_id": project_follow.id
                }
            )
            
            return Response(
                ProjectFollowSerializer(project_follow).data,
                status=status.HTTP_201_CREATED
            )
            
        except IntegrityError:
            return Response(
                {"detail": "You are already following this project."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(
                f"Error creating project follow: {str(e)}",
                extra={
                    "investor_id": getattr(request.user, 'investor', {}).get('id'),
                    "project_id": project.id
                },
                exc_info=True
            )
            return Response(
                {"detail": "An error occurred while following the project."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProjectFollowListView(ListAPIView):
    """
    API view for listing project follows for the authenticated investor.
    
    GET /api/v1/investments/follows/
    """
    serializer_class = ProjectFollowSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedInvestor403, HasActiveCompanyAccount]
    pagination_class = pagination.PageNumberPagination

    def get_queryset(self):
        """Return active project follows for the authenticated investor."""
        return ProjectFollow.objects.filter(
            investor=self.request.user.investor,
            is_active=True
        ).select_related(
            'investor__user',
            'project__startup'
        ).order_by('-followed_at')


class ProjectFollowDetailView(RetrieveUpdateAPIView):
    """
    API view for retrieving and updating (unfollowing) project follows.
    
    GET /api/v1/investments/follows/{id}/
    PATCH /api/v1/investments/follows/{id}/ (for unfollowing)
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedInvestor403, HasActiveCompanyAccount]

    def get_queryset(self):
        """Return project follows for the authenticated investor."""
        return ProjectFollow.objects.filter(
            investor=self.request.user.investor
        ).select_related(
            'investor__user',
            'project__startup'
        )

    def get_serializer_class(self):
        """Return ProjectFollowSerializer for all operations."""
        return ProjectFollowSerializer

    def patch(self, request, *args, **kwargs):
        """Handle unfollowing a project (soft delete)."""
        instance = self.get_object()
        
        if not instance.is_active:
            return Response(
                {"detail": "You are not currently following this project."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        
        logger.info(
            f"Project unfollowed: investor={request.user.investor.id}, project={instance.project.id}",
            extra={
                "investor_id": request.user.investor.id,
                "project_id": instance.project.id,
                "project_follow_id": instance.id
            }
        )
        
        return Response(
            {"detail": "Successfully unfollowed the project."},
            status=status.HTTP_200_OK
        )


class ProjectFollowersListView(ListAPIView):
    """
    API view for listing followers of a specific project.
    
    This view is intended for startup owners to see who is following their projects.
    
    GET /api/v1/projects/{project_id}/followers/
    """
    serializer_class = ProjectFollowSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedOr401]
    pagination_class = pagination.PageNumberPagination

    def get_queryset(self):
        """Return active followers for the specified project."""
        project_id = self.kwargs.get('project_id')
        
        try:
            project = get_object_or_404(Project, id=project_id)
        except (ValueError, Project.DoesNotExist):
            return ProjectFollow.objects.none()
        
        return ProjectFollow.objects.filter(
            project=project,
            is_active=True
        ).select_related(
            'investor__user',
            'project__startup'
        ).order_by('-followed_at')