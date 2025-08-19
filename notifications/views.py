from rest_framework import viewsets, permissions, decorators, response, status
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing and updating notifications.
    - Allows startup owners to list their notifications.
    - Allows marking a notification as read.
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @decorators.action(detail=True, methods=["patch"])
    def read(self, request, pk=None):
        notif = self.get_queryset().filter(pk=pk).first()
        if not notif:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return response.Response(self.get_serializer(notif).data)

    @decorators.action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        qs = self.get_queryset().filter(is_read=False)
        qs.update(is_read=True)
        return response.Response({"updated": qs.count()})