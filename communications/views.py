import logging

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from users.cookie_jwt import CookieJWTAuthentication
from users.permissions import IsAuthenticatedOr401
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


class DefaultPageNumberPagination(PageNumberPagination):
    page_size = 10

logger = logging.getLogger(__name__)


def _parse_bool(val):
    """Parse a value into a boolean, accepting various string representations."""
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
    permission_classes = [IsAuthenticatedOr401]
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
    permission_classes = [IsAuthenticatedOr401]
    pagination_class = None


class UserNotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to view and update their notification preferences.
    """
    serializer_class = UserNotificationPreferenceSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedOr401]
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

    @action(detail=True, methods=['patch'], url_path='email-preferences')
    def update_email_preferences(self, request, pk=None):
        """
        Update email notification preferences.
        
        This endpoint allows startups to opt-in or opt-out of receiving email notifications.
        
        Parameters:
        - enable_email: Boolean to globally enable/disable all email notifications
        - type_preferences: Optional list of notification type preferences with format:
          [{"notification_type_id": 1, "frequency": "immediate|daily_digest|weekly_summary|disabled"}]
          
        Returns the updated notification preferences.
        """
        preference = self.get_object()
        enable_email = request.data.get('enable_email')
        if enable_email is not None:
            parsed_value = _parse_bool(enable_email)
            if parsed_value is None:
                return Response(
                    {'error': 'enable_email must be a boolean value'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            preference.enable_email = parsed_value
            preference.save(update_fields=['enable_email', 'updated_at'])
            logger.info(
                "notifications.update_email_preferences user=%s enable_email=%s",
                getattr(request.user, 'user_id', getattr(request.user, 'id', None)),
                parsed_value,
            )
        
        type_preferences = request.data.get('type_preferences', [])
        if type_preferences and not isinstance(type_preferences, list):
            return Response(
                {'error': 'type_preferences must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        updated_types = []
        errors = []
        
        for i, type_pref_data in enumerate(type_preferences):
            if not isinstance(type_pref_data, dict):
                errors.append({
                    'index': i,
                    'error': 'Each type preference must be an object'
                })
                continue
                
            notification_type_id = type_pref_data.get('notification_type_id')
            frequency = type_pref_data.get('frequency')
            
            if not notification_type_id:
                errors.append({
                    'index': i,
                    'error': 'notification_type_id is required'
                })
                continue
                
            if not frequency:
                errors.append({
                    'index': i,
                    'error': 'frequency is required'
                })
                continue
                
            try:
                nt_id = int(notification_type_id)
            except (TypeError, ValueError):
                errors.append({
                    'index': i,
                    'error': 'notification_type_id must be an integer'
                })
                continue
                
            type_pref = preference.type_preferences.filter(notification_type_id=nt_id).first()
            if not type_pref:
                errors.append({
                    'index': i,
                    'error': f'Notification type preference with id {nt_id} not found'
                })
                continue
                
            old_frequency = type_pref.frequency
            serializer = UserNotificationTypePreferenceSerializer(
                type_pref,
                data={'frequency': frequency},
                partial=True,
                context={'request': request},
            )
            if not serializer.is_valid():
                errors.append({
                    'index': i,
                    'error': serializer.errors
                })
                continue
                
            serializer.save()
            updated_types.append(nt_id)
            logger.info(
                "notifications.update_email_type_preference user=%s notification_type_id=%s %s->%s",
                getattr(request.user, 'user_id', getattr(request.user, 'id', None)),
                nt_id,
                old_frequency,
                serializer.instance.frequency,
            )
        response_data = self.get_serializer(preference).data
        if errors:
            response_data['errors'] = errors
        if updated_types:
            response_data['updated_types'] = updated_types
            
        if errors:
            if len(errors) == 1:
                response_data['error'] = errors[0]['error']
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(response_data)

    @action(detail=False, methods=['get'], url_path='email-preferences')
    def get_email_preferences(self, request):
        """
        Get the current user's email notification preferences.
        
        This endpoint returns a dedicated view of the user's notification preferences
        specific to email notifications, formatted to make it easy for startups
        to manage their email notification settings.
        
        Returns:
        - enable_email: Boolean indicating if email notifications are globally enabled
        - notification_types: List of notification types with their current preferences
          [
            {
              "id": 1,
              "code": "new_follower",
              "name": "New Follower",
              "description": "When someone follows your startup",
              "frequency": "immediate",
              "is_active": true
            }
          ]
        """
        preference = self.get_object()
        notification_types = []
        for type_pref in preference.type_preferences.select_related('notification_type').all():
            nt = type_pref.notification_type
            notification_types.append({
                'id': nt.id,
                'code': nt.code,
                'name': nt.name,
                'description': nt.description,
                'frequency': type_pref.frequency,
                'is_active': nt.is_active
            })
            
        return Response({
            'enable_email': preference.enable_email,
            'notification_types': notification_types
        })

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
