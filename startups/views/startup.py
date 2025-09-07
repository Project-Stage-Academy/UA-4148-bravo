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
from users.permissions import IsStartupUser, CanCreateCompanyPermission, IsAuthenticatedOr401, HasActiveCompanyAccount
from communications.serializers import (
    UserNotificationPreferenceSerializer,
    UserNotificationTypePreferenceSerializer,
    UpdateTypePreferenceSerializer,
)
from communications.services import get_or_create_user_pref


class StartupViewSet(BaseValidatedModelViewSet):
    queryset = Startup.objects.select_related('user', 'industry', 'location') \
        .prefetch_related('projects')

    serializer_class = StartupSerializer
    permission_classes = [IsAuthenticatedOr401, IsStartupUser, HasActiveCompanyAccount]
    authentication_classes = [CookieJWTAuthentication]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['industry', 'stage', 'location__country']
    search_fields = ['company_name', 'user__first_name', 'user__last_name', 'email']

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
            return Response({'notification_type_id': ['A valid integer is required.']},
                            status=status.HTTP_400_BAD_REQUEST)

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
                            return Response({'error': 'Notification type preference not found'},
                                            status=status.HTTP_404_NOT_FOUND)
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
            return Response({'notification_type_id': ['A valid integer is required.']},
                            status=status.HTTP_400_BAD_REQUEST)

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
                            return Response({'error': 'Notification type preference not found'},
                                            status=status.HTTP_404_NOT_FOUND)
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
        return [IsAuthenticatedOr401(), IsStartupUser()]

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the request action.
        """
        if self.action == 'create':
            return StartupCreateSerializer
        return StartupSerializer
