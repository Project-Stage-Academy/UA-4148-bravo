from django.db.models import Q
from django.urls import reverse
from rest_framework import serializers
from .models import (
    Notification, 
    UserNotificationPreference,
    NotificationType,
    UserNotificationTypePreference,
    NotificationTrigger,
)
from investors.models import Investor

class NotificationTypeSerializer(serializers.ModelSerializer):
    """Serializer for notification types."""
    class Meta:
        model = NotificationType
        fields = ['id', 'code', 'name', 'description', 'is_active']
        read_only_fields = ['id', 'code'] 


class NotificationFrequencyField(serializers.ChoiceField):
    """Custom field for notification frequency choices."""
    def __init__(self, **kwargs):
        from .models import NotificationFrequency
        kwargs.setdefault('choices', NotificationFrequency.choices)
        super().__init__(**kwargs)


class UserNotificationTypePreferenceSerializer(serializers.ModelSerializer):
    """Serializer for the UserNotificationTypePreference model."""
    notification_type = NotificationTypeSerializer(read_only=True)
    notification_type_id = serializers.PrimaryKeyRelatedField(
        source='notification_type',
        write_only=True,
        queryset=NotificationType.objects.none()
    )
    frequency = NotificationFrequencyField()
    
    class Meta:
        model = UserNotificationTypePreference
        fields = [
            'id', 'notification_type', 'notification_type_id', 
            'frequency', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'notification_type', 'created_at', 'updated_at']
    
    def get_fields(self):
        """
        Dynamically set queryset for notification_type_id field.
        - For updates: Allow current notification type (even if inactive) + all active types
        - For creation: Only allow active notification types
        """
        fields = super().get_fields()
        
        if self.instance and getattr(self.instance, 'notification_type_id', None):
            queryset = NotificationType.objects.filter(
                Q(is_active=True) | Q(pk=self.instance.notification_type_id)
            )
        else:
            queryset = NotificationType.objects.filter(is_active=True)
            
        fields['notification_type_id'].queryset = queryset
        return fields


class UserNotificationPreferenceSerializer(serializers.ModelSerializer):
    """    
    Serializer for the UserNotificationPreference model.
    Handles both creation and updates of notification preferences.
    The user is automatically set from the request context on creation.
    """
    type_preferences = UserNotificationTypePreferenceSerializer(
        source='type_preferences.all',
        many=True,
        read_only=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        read_only=True
    )
    
    class Meta:
        model = UserNotificationPreference
        fields = [
            'user_id', 'enable_in_app', 'enable_email', 'enable_push',
            'type_preferences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user_id', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create notification preferences for the authenticated user."""
        request = self.context.get('request')
        
        if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
            raise serializers.ValidationError('Authentication required for creating preferences.')
        
        validated_data['user'] = request.user
        
        if UserNotificationPreference.objects.filter(user=request.user).exists():
            raise serializers.ValidationError(
                'Notification preferences already exist for this user.'
            )
            
        return super().create(validated_data)


    def update(self, instance, validated_data):
        """Update notification preference fields."""
        update_fields = ['enable_in_app', 'enable_email', 'enable_push']
        for field in update_fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        instance.save()
        return instance


class UpdateTypePreferenceSerializer(serializers.Serializer):
    """Serializer to validate and apply per-type preference updates.

    Expects context['pref'] with the user's UserNotificationPreference instance.
    On save(), updates and returns the matching UserNotificationTypePreference.
    """
    notification_type_id = serializers.IntegerField()
    frequency = NotificationFrequencyField()

    def validate(self, attrs):
        pref = self.context.get('pref')
        if pref is None:
            raise serializers.ValidationError('Preference context is required')
        nt_id = attrs.get('notification_type_id')
        type_pref = pref.type_preferences.filter(notification_type_id=nt_id).first()
        if not type_pref:
            raise serializers.ValidationError('Notification type preference not found', code='not_found')
        attrs['type_pref'] = type_pref
        return attrs

    def save(self, **kwargs):
        type_pref = self.validated_data['type_pref']
        type_pref.frequency = self.validated_data['frequency']
        type_pref.save()
        return type_pref

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""
    notification_type = NotificationTypeSerializer(read_only=True)
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    actor = serializers.SerializerMethodField(read_only=True)
    redirect = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'notification_id',
            'notification_type',
            'title',
            'message',
            'is_read',
            'priority',
            'priority_display',
            'actor',
            'redirect',
            'created_at',
            'updated_at',
            'expires_at',
        ]
        read_only_fields = [
            'notification_id', 'created_at', 'updated_at'
        ]

    def _get_investor_from_user(self, user):
        """Return Investor instance for a user, if present, else None."""
        try:
            investor = user.investor 
        except (Investor.DoesNotExist, AttributeError):
            return None
        return investor if isinstance(investor, Investor) else None

    def get_actor(self, obj):
        """Return actor details for the notification trigger.
        Includes investor details if the triggering user is an investor.
        """
        actor = {
            'type': obj.triggered_by_type,
            'user_id': getattr(obj, 'triggered_by_user_id', None),
            'investor_id': None,
            'display_name': None,
        }
        user = getattr(obj, 'triggered_by_user', None)
        if user:
            investor = self._get_investor_from_user(user)
            if investor:
                actor['investor_id'] = investor.pk
                actor['display_name'] = getattr(investor, 'company_name', None)
            else:
                first = getattr(user, 'first_name', '') or ''
                last = getattr(user, 'last_name', '') or ''
                full = (first + ' ' + last).strip()
                actor['display_name'] = full or None
        return actor

    def get_redirect(self, obj):
        """Compute a redirect target the frontend can use to navigate users.
        Priority order: message -> project -> startup -> investor. Returns None if not applicable.
        """
        for field, kind in [
            ('related_message_id', 'message'),
            ('related_project_id', 'project'),
            ('related_startup_id', 'startup'),
        ]:
            rid = getattr(obj, field, None)
            if not rid:
                continue
            url = None
            if kind == 'project':
                try:
                    url = reverse('project-detail', kwargs={'pk': rid})
                except Exception:
                    url = f"/projects/{rid}"
            elif kind == 'startup':
                try:
                    url = reverse('startup-detail', kwargs={'pk': rid})
                except Exception:
                    url = f"/startups/{rid}"
            elif kind == 'message':
                url = f"/messages/{rid}"
            return {'kind': kind, 'id': rid, 'url': url}

        user = getattr(obj, 'triggered_by_user', None)
        if user and getattr(obj, 'triggered_by_type', None) == NotificationTrigger.INVESTOR:
            investor = self._get_investor_from_user(user)
            if investor:
                try:
                    url = reverse('investor-detail', kwargs={'pk': investor.pk})
                except Exception:
                    url = f"/investors/{investor.pk}"
                return {'kind': 'investor', 'id': investor.pk, 'url': url}
        return None
