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
from communications.views import _parse_bool

class StartupViewSet(BaseValidatedModelViewSet):
    queryset = Startup.objects.select_related('user', 'industry', 'location') \
        .prefetch_related('projects')
    
    serializer_class = StartupSerializer
    permission_classes = [IsAuthenticatedOr401, IsStartupUser]
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

    @action(detail=False, methods=['get'], url_path='preferences/email-preferences', url_name='email-preferences-get')
    def get_email_preferences(self, request):
        """
        Get the current startup user's email notification preferences.
        
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
        preference = self._get_or_create_user_pref(request)
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

    @action(detail=False, methods=['patch'], url_path='preferences/email-preferences', url_name='email-preferences-update')
    def update_email_preferences(self, request):
        """
        Update email notification preferences for the current startup user.
        
        This endpoint allows startups to opt-in or opt-out of receiving email notifications.
        
        Parameters:
        - enable_email: Boolean to globally enable/disable all email notifications
        - type_preferences: Optional list of notification type preferences with format:
          [{"notification_type_id": 1, "frequency": "immediate|daily_digest|weekly_summary|disabled"}]
          
        Returns the updated notification preferences.
        """
        preference = self._get_or_create_user_pref(request)
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
            
        response_data = UserNotificationPreferenceSerializer(preference, context={'request': request}).data
        if updated_types:
            response_data['updated_types'] = updated_types
            
        if errors:
            response_data['errors'] = errors
            response_data['error'] = 'One or more type preferences have invalid values'
            if len(errors) == len(type_preferences):
                # All updates failed
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(response_data)

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