import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    Notification,
    UserNotificationPreference,
    NotificationType,
    UserNotificationTypePreference
)
from .serializers import (
    NotificationSerializer,
    UserNotificationPreferenceSerializer,
    NotificationTypeSerializer,
    UserNotificationTypePreferenceSerializer
)

logger = logging.getLogger(__name__)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'notification_id'
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        """Return only the authenticated user's notifications."""
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get the count of unread notifications for the current user."""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, notification_id=None):
        """
        Mark a notification as read.

        Response: {"status": "notification marked as read"}
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        
        logger.info(
            "notifications.mark_as_read user=%s notification_id=%s",
            getattr(request.user, 'user_id', getattr(request.user, 'id', None)),
            str(notification.notification_id),
        )
        return Response({'status': 'notification marked as read'})
    
    @action(detail=False, methods=['post'])
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


class NotificationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows notification types to be viewed.
    Requires authentication.
    """
    queryset = NotificationType.objects.filter(is_active=True)
    serializer_class = NotificationTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None


class UserNotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to view and update their notification preferences.
    """
    serializer_class = UserNotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
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
