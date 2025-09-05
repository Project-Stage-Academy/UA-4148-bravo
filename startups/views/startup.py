from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound
from startups.models import Startup
from startups.serializers.startup_full import StartupSerializer
from startups.serializers.startup_create import StartupCreateSerializer
from startups.views.startup_base import BaseValidatedModelViewSet
from users.cookie_jwt import CookieJWTAuthentication
from users.permissions import IsStartupUser, CanCreateCompanyPermission, IsAuthenticatedOr401
from communications.serializers import (
    UserNotificationPreferenceSerializer,
    UserNotificationTypePreferenceSerializer,
    UpdateTypePreferenceSerializer,
)
from communications.services import get_or_create_user_pref
from startups.serializers.startup_list import StartupListSerializer
from startups.serializers.startup_detail import StartupDetailSerializer
from decimal import Decimal, InvalidOperation
from django.db.models import Q
from rest_framework.filters import OrderingFilter
from rest_framework import status
from startups.filters import StartupFilter
from django_filters import rest_framework as filters
from startups.filters import StartupFilter

class StartupViewSet(BaseValidatedModelViewSet):
    queryset = Startup.objects.select_related('user', 'industry', 'location') \
        .prefetch_related('projects')
    
    serializer_class = StartupListSerializer
    permission_classes = [IsAuthenticatedOr401]
    authentication_classes = [CookieJWTAuthentication]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = StartupFilter 
    search_fields = ['company_name', 'user__first_name', 'user__last_name', 'email', 'industry__name']

    def _get_or_create_user_pref(self, request):
        """Fetch the current user's notification preferences, creating defaults if absent.
        Delegates to communications.services.get_or_create_user_pref to avoid duplication and
        to seed type preferences using each NotificationType.default_frequency.
        """
        return get_or_create_user_pref(request.user)

    @action(detail=False, methods=['get', 'patch'], url_path='preferences', url_name='preferences')
    def preferences(self, request):
        """Get or update the current startup user's notification channel preferences."""
        pref = self._get_or_create_user_pref(request)

        if request.method.lower() == 'get':
            serializer = UserNotificationPreferenceSerializer(pref, context={'request': request})
            return Response(serializer.data)

        # PATCH
        serializer = UserNotificationPreferenceSerializer(
            pref,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], url_path='preferences/update_type', url_name='preferences-update-type')
    def update_type_preference(self, request):
        """Update the frequency for a specific notification type for the current startup user."""
        pref = self._get_or_create_user_pref(request)

        notification_type_id = request.data.get('notification_type_id')
        frequency = request.data.get('frequency')

        if notification_type_id is None or frequency is None:
            errors = {}
            if notification_type_id is None:
                errors['notification_type_id'] = ['This field is required.']
            if frequency is None:
                errors['frequency'] = ['This field is required.']
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            nt_id = int(notification_type_id)
        except (TypeError, ValueError):
            return Response({'notification_type_id': ['A valid integer is required.']}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UpdateTypePreferenceSerializer(
            data={'notification_type_id': nt_id, 'frequency': frequency},
            context={'pref': pref},
        )
        try:
            if not serializer.is_valid():
                errors = serializer.errors
                non_field = errors.get('non_field_errors') if isinstance(errors, dict) else None
                if non_field:
                    for err in non_field:
                        code = getattr(err, 'code', None)
                        if code == 'not_found' or str(err) == 'Notification type preference not found':
                            return Response({'error': 'Notification type preference not found'}, status=status.HTTP_404_NOT_FOUND)
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        except NotFound:
            return Response({'error': 'Notification type preference not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as exc:
            detail = getattr(exc, 'detail', None)
            return Response(detail or serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        type_pref = serializer.save()
        return Response(UserNotificationTypePreferenceSerializer(type_pref, context={'request': request}).data)


    def _get_or_create_user_pref(self, request):
        """Fetch the current user's notification preferences, creating defaults if absent.
        Delegates to communications.services.get_or_create_user_pref to avoid duplication and
        to seed type preferences using each NotificationType.default_frequency.
        """
        return get_or_create_user_pref(request.user)

    @action(detail=False, methods=['get', 'patch'], url_path='preferences', url_name='preferences')
    def preferences(self, request):
        """Get or update the current startup user's notification channel preferences."""
        pref = self._get_or_create_user_pref(request)

        if request.method.lower() == 'get':
            serializer = UserNotificationPreferenceSerializer(pref, context={'request': request})
            return Response(serializer.data)

        # PATCH
        serializer = UserNotificationPreferenceSerializer(
            pref,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], url_path='preferences/update_type', url_name='preferences-update-type')
    def update_type_preference(self, request):
        """Update the frequency for a specific notification type for the current startup user."""
        pref = self._get_or_create_user_pref(request)

        notification_type_id = request.data.get('notification_type_id')
        frequency = request.data.get('frequency')

        if notification_type_id is None or frequency is None:
            errors = {}
            if notification_type_id is None:
                errors['notification_type_id'] = ['This field is required.']
            if frequency is None:
                errors['frequency'] = ['This field is required.']
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            nt_id = int(notification_type_id)
        except (TypeError, ValueError):
            return Response({'notification_type_id': ['A valid integer is required.']}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UpdateTypePreferenceSerializer(
            data={'notification_type_id': nt_id, 'frequency': frequency},
            context={'pref': pref},
        )
        try:
            if not serializer.is_valid():
                errors = serializer.errors
                non_field = errors.get('non_field_errors') if isinstance(errors, dict) else None
                if non_field:
                    for err in non_field:
                        code = getattr(err, 'code', None)
                        if code == 'not_found' or str(err) == 'Notification type preference not found':
                            return Response({'error': 'Notification type preference not found'}, status=status.HTTP_404_NOT_FOUND)
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        except NotFound:
            return Response({'error': 'Notification type preference not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as exc:
            detail = getattr(exc, 'detail', None)
            return Response(detail or serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        type_pref = serializer.save()
        return Response(UserNotificationTypePreferenceSerializer(type_pref, context={'request': request}).data)


    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            return [IsAuthenticatedOr401(), CanCreateCompanyPermission()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsAuthenticatedOr401(), IsStartupUser()]
        if self.action in ('preferences', 'update_type_preference'):
            return [IsAuthenticatedOr401(), IsStartupUser()]
        return [IsAuthenticatedOr401()]

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the request action.
        """
        if self.action == 'create':
            return StartupCreateSerializer
        return StartupSerializer
    
    def _to_bool(self, val: str) -> bool:
        return str(val).lower() in ('1', 'true', 'yes', 'y')

    def get_queryset(self):
        qs = Startup.objects.select_related('user', 'industry', 'location').prefetch_related('projects')

        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            qs = qs.filter(Q(is_public=True) | Q(user=user))
        else:
            qs = qs.filter(is_public=True)

        params = self.request.query_params

        industry_name = params.get('industry')
        if industry_name:
            qs = qs.filter(industry__name__iexact=industry_name)

        min_team = params.get('min_team_size')
        if min_team:
            try:
                qs = qs.filter(team_size__gte=int(min_team))
            except (TypeError, ValueError):
                return Startup.objects.none()

        fn_lte = params.get('funding_needed__lte')
        if fn_lte:
            try:
                qs = qs.filter(funding_needed__lte=Decimal(fn_lte))
            except (InvalidOperation, TypeError):
                return Startup.objects.none()

        is_verified = params.get('is_verified')
        if is_verified is not None:
            qs = qs.filter(is_verified=self._to_bool(is_verified))

        country = params.get('country')
        if country:
            qs = qs.filter(location__country=country)

        city = params.get('city')
        if city:
            qs = qs.filter(location__city__iexact=city)

        return qs
