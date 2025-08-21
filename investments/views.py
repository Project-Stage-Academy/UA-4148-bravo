from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction  
from django.db.models import F
import logging

from investments.models import Subscription
from investments.serializers.subscription_create import SubscriptionCreateSerializer
from users.permissions import IsInvestor

logger = logging.getLogger(__name__)

class SubscriptionCreateView(CreateAPIView):
    """
    API endpoint for creating a new investment subscription.

    - Requires authentication and investor role.
    - Validates funding constraints and prevents invalid investments.
    - Returns project funding status along with subscription details.
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionCreateSerializer
    permission_classes = [IsAuthenticated, IsInvestor]

    def create(self, request, *args, **kwargs):  
        # try:
            serializer = self.get_serializer(data=request.data)  
            serializer.is_valid(raise_exception=True)  

            with transaction.atomic():  
                subscription = serializer.save()  
                project = subscription.project  
                project.refresh_from_db()  

                project.current_funding = F('current_funding') + subscription.amount  
                project.save(update_fields=['current_funding'])  
                project.refresh_from_db()  

                remaining_funding = project.funding_goal - project.current_funding
                project_status = "Fully funded" if remaining_funding <= 0 else "Partially funded"

                logger.info(
                    "Subscription created successfully for project %s by user %s",
                    project.id,
                    request.user.id,
                )

            return Response(
                {
                    "message": "Subscription created successfully.",
                    "remaining_funding": remaining_funding,
                    "project_status": project_status,
                    "subscription_id": subscription.id,
                },
                status=status.HTTP_201_CREATED,
            )
        # except Exception as e:
        #     logger.exception("Failed to create subscription for user %s", getattr(request.user, 'id', None))
        #     return Response({"detail": "Failed to create subscription. Please try again."}, status=status.HTTP_400_BAD_REQUEST)
