import logging

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import viewsets, status, mixins, serializers
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from users.cookie_jwt import CookieJWTAuthentication
from users.permissions import HasActiveCompanyAccount
from .models import (
    Notification,
    UserNotificationPreference,
    NotificationType,
    UserNotificationTypePreference,
    EmailNotificationPreference,
    EmailNotificationTypePreference
)
from .serializers import (
    NotificationSerializer,
    UserNotificationPreferenceSerializer,
    NotificationTypeSerializer,
    UserNotificationTypePreferenceSerializer,
    EmailNotificationPreferenceSerializer
)


class DefaultPageNumberPagination(PageNumberPagination):
    page_size = 10


logger = logging.getLogger(__name__)


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    ViewSet for managing user notifications.
    """
    serializer_class = NotificationSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, HasActiveCompanyAccount]
    lookup_field = 'notification_id'
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        """Return only the authenticated user's notifications with helpful joins and filters.

        Supported query params:
        - is_read: 'true' | 'false'
        - type: notification type code (slug)
        - priority: 'low' | 'medium' | 'high'
        - created_after, created_before: ISO datetime strings
        """
        qs = (
            Notification.objects
            .filter(user=self.request.user)
            .select_related('notification_type', 'triggered_by_user')
        )

        params = self.request.query_params

        def _parse_bool(val):
            if isinstance(val, bool):
                return val
            if val is None:
                return None
            s = str(val).strip().lower()
            if s in {'1', 'true', 'yes'}:
                return True
            if s in {'0', 'false', 'no'}:
                return False
            return None

        is_read_param = _parse_bool(params.get('is_read'))
        if is_read_param is not None:
            qs = qs.filter(is_read=is_read_param)

        ntype_code = params.get('type')
        if ntype_code:
            qs = qs.filter(notification_type__code=ntype_code)

        priority = params.get('priority')
        if priority in {'low', 'medium', 'high'}:
            qs = qs.filter(priority=priority)

        created_after = params.get('created_after')
        if created_after:
            dt = parse_datetime(created_after)
            if dt:
                qs = qs.filter(created_at__gte=dt)

        created_before = params.get('created_before')
        if created_before:
            dt = parse_datetime(created_before)
            if dt:
                qs = qs.filter(created_at__lte=dt)

        return qs

    @action(detail=False, methods=['get'], url_path='unread_count')
    def unread_count(self, request):
        """Get the count of unread notifications for the current user."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})

    @action(detail=True, methods=['post'], url_path='mark_as_read')
    def mark_as_read(self, request, notification_id=None):
        """
        Mark a notification as read.

        Response: {"status": "notification marked as read"}
        """
        notification = self.get_object()
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read', 'updated_at'])

        logger.info(
            "notifications.mark_as_read user=%s notification_id=%s",
            getattr(request.user, 'user_id', getattr(request.user, 'id', None)),
            str(notification.notification_id),
        )
        return Response({'status': 'notification marked as read'})

    @action(detail=True, methods=['post'], url_path='mark_as_unread')
    def mark_as_unread(self, request, notification_id=None):
        """
        Mark a notification as unread.

        Response: {"status": "notification marked as unread"}
        """
        notification = self.get_object()
        if notification.is_read:
            notification.is_read = False
            notification.save(update_fields=['is_read', 'updated_at'])
        logger.info(
            "notifications.mark_as_unread user=%s notification_id=%s",
            getattr(request.user, 'user_id', getattr(request.user, 'id', None)),
            str(notification.notification_id),
        )
        return Response({'status': 'notification marked as unread'})

    @action(detail=False, methods=['post'], url_path='mark_all_as_read')
    def mark_all_as_read(self, request):
        """
        Mark all notifications as read for the current user.

        Response: {"status": "marked <n> notifications as read"}
        """
        now = timezone.now()
        updated = self.get_queryset().filter(is_read=False).update(is_read=True, updated_at=now)
        # Audit log
        logger.info(
            "notifications.mark_all_as_read user=%s updated=%d",
            getattr(request.user, 'user_id', getattr(request.user, 'id', None)),
            updated,
        )
        return Response({'status': f'marked {updated} notifications as read'})

    @action(detail=False, methods=['post'], url_path='mark_all_as_unread')
    def mark_all_as_unread(self, request):
        """
        Mark all notifications as unread for the current user.

        Response: {"status": "marked <n> notifications as unread"}
        """
        now = timezone.now()
        updated = self.get_queryset().filter(is_read=True).update(is_read=False, updated_at=now)
        logger.info(
            "notifications.mark_all_as_unread user=%s updated=%d",
            getattr(request.user, 'user_id', getattr(request.user, 'id', None)),
            updated,
        )
        return Response({'status': f'marked {updated} notifications as unread'})

    @action(detail=True, methods=['get'], url_path='resolve')
    def resolve(self, request, notification_id=None):
        """
        Return just the redirect payload for the notification to help lightweight clients.

        Response: {"redirect": {...}}
        """
        notification = self.get_object()
        serializer = self.get_serializer(notification)
        data = serializer.data.get('redirect')
        return Response({'redirect': data})


class NotificationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows notification types to be viewed.
    Requires authentication.
    """
    queryset = NotificationType.objects.filter(is_active=True)
    serializer_class = NotificationTypeSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, HasActiveCompanyAccount]
    pagination_class = None


class UserNotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to view and update their notification preferences.
    """
    serializer_class = UserNotificationPreferenceSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, HasActiveCompanyAccount]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        """Return only the current user's preferences."""
        return UserNotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        """
        Return the current user's preferences, creating them if they don't exist.
        """
        queryset = self.filter_queryset(self.get_queryset())
        obj = queryset.first()

        if obj is None:
            obj = UserNotificationPreference.objects.create(user=self.request.user)

            notification_types = NotificationType.objects.filter(is_active=True)
            for notification_type in notification_types:
                UserNotificationTypePreference.objects.create(
                    user_preference=obj,
                    notification_type=notification_type,
                    frequency='immediate'
                )

        return obj

    @action(detail=True, methods=['patch'])
    def update_type_preference(self, request, pk=None):
        """
        Update a specific notification type preference.
        Expected payload: {"notification_type_id": 1, "frequency": "immediate"}
        Errors: 400 (validation), 404 (preference not found)
        """
        preference = self.get_object()
        notification_type_id = request.data.get('notification_type_id')
        frequency = request.data.get('frequency')

        if notification_type_id is None or frequency is None:
            return Response(
                {'error': 'notification_type_id and frequency are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            nt_id = int(notification_type_id)
        except (TypeError, ValueError):
            return Response(
                {'error': 'notification_type_id must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        type_pref = preference.type_preferences.filter(notification_type_id=nt_id).first()
        if not type_pref:
            return Response(
                {'error': 'Notification type preference not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        old_frequency = type_pref.frequency
        serializer = UserNotificationTypePreferenceSerializer(
            type_pref,
            data={'frequency': frequency},
            partial=True,
            context={'request': request},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        # Audit log
        logger.info(
            "notifications.update_type_preference user=%s notification_type_id=%s %s->%s",
            getattr(request.user, 'user_id', getattr(request.user, 'id', None)),
            nt_id,
            old_frequency,
            serializer.instance.frequency,
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='options', url_name='preference-options')
    def preference_options(self, request):
        """
        Return business-level options for notification preferences (not HTTP OPTIONS).

        Currently returns available frequency choices.
        """
        from .models import NotificationFrequency

        return Response({
            'frequencies': [
                {'value': choice[0], 'display': str(choice[1])}
                for choice in NotificationFrequency.choices
            ]
        })


class EmailNotificationPreferenceViewSet(viewsets.GenericViewSet,
                                         mixins.RetrieveModelMixin,
                                         mixins.UpdateModelMixin,
                                         mixins.ListModelMixin):
    """
    API endpoint for managing email notification preferences.
    
    This ViewSet provides endpoints for managing user email notification preferences,
    separate from the general notification preferences system.
    """
    serializer_class = EmailNotificationPreferenceSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated, HasActiveCompanyAccount]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        """Return only the current user's preferences."""
        return EmailNotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        """
        Return the current user's preferences, creating them if they don't exist.
        """
        queryset = self.filter_queryset(self.get_queryset())
        obj = queryset.first()

        if obj is None:
            obj = EmailNotificationPreference.objects.create(user=self.request.user)

            notification_types = NotificationType.objects.filter(is_active=True)
            for notification_type in notification_types:
                EmailNotificationTypePreference.objects.create(
                    email_preference=obj,
                    notification_type=notification_type,
                    enabled=True
                )

        return obj

    def list(self, request, *args, **kwargs):
        """
        Get the user's email notification preferences.
        Will create preferences if they don't exist yet.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Update email notification type preferences.
        
        Expected payload:
        {
            "types_enabled": [
                {"notification_type_id": 1, "enabled": true},
                {"notification_type_id": 2, "enabled": false}
            ]
        }
        """
        instance = self.get_object()

        types_enabled_data = request.data.get('types_enabled', [])
        if not isinstance(types_enabled_data, list):
            return Response(
                {'error': 'types_enabled must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(instance, data=request.data, context={'request': request})

        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except serializers.ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
