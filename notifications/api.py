from rest_framework import viewsets, mixins, permissions, status, decorators
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for viewing and updating notifications.
    - Allows startup owners to list their notifications.
    - Allows marking a notification as read.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Notification.objects
            .filter(startup__user=self.request.user)
            .order_by("-created_at")
        )

    @decorators.action(detail=True, methods=["patch"], url_path="read", url_name="read")
    def read(self, request, pk=None):
        notif = get_object_or_404(Notification, pk=pk)

        if not notif.startup or notif.startup.user_id != request.user.id:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        if not notif.is_read:
            notif.is_read = True
            notif.save(update_fields=["is_read"])

        return Response(status=status.HTTP_204_NO_CONTENT)
