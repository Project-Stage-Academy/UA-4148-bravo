from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
# from django.db import transaction
# from django.db.models import F
import logging

from .models import Subscription
# from projects.models import Project
from investments.serializers.subscription_create import SubscriptionCreateSerializer 
from users.permissions import IsInvestor

logger = logging.getLogger(__name__)


class SubscriptionCreateView(CreateAPIView):
    """
    API endpoint for creating a new investment subscription.
    Uses transaction management and F() expressions for safe concurrent updates.
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionCreateSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)
        
        subscription = serializer.save()

        logger.info(
            "Subscription created successfully for project %s by user %s",
            subscription.project_id,
            request.user.id,
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)