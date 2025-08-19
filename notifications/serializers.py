from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    Exposes basic fields needed for API responses, including related investor
    and startup IDs, read status, and creation timestamp.
    """
    class Meta:
        model = Notification
        fields = ["id", "type", "title", "body", "is_read", "created_at", "investor_id", "startup_id"]