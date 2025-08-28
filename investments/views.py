from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status
import logging

from rest_framework.permissions import IsAuthenticated
from .models import Subscription
from projects.models import Project
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
        project_id = self.kwargs["project_id"]
        try:
            self.project = Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            return Response(
                {"project": "Project does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(data=request.data, context={"request": request, "project": self.project})
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
            subscription = serializer.instance

            self.project.current_funding += subscription.amount
            self.project.save()
            remaining_funding = self.project.funding_goal - self.project.current_funding
            project_status = "Fully funded" if remaining_funding <= 0 else "Partially funded"

            logger.info(
                "Subscription created successfully for project %s by user %s",
                self.project.id,
                request.user.id,
            )

            return Response(
                {
                    "message": "Subscription created successfully.",
                    "remaining_funding": remaining_funding,
                    "project_status": project_status,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception:
            logger.exception("Failed to create subscription for user %s", getattr(request.user, 'id', None))
            return Response(
                {"detail": "Failed to create subscription. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
    def perform_create(self, serializer):
        """
        Persist a new subscription instance.

        - Retrieves the target project using the `project_id` from the URL.
        - Associates the subscription with the authenticated investor (`request.user.investor`).
        - Saves the subscription via the serializer.
        """
        serializer.save(
            investor=self.request.user.investor,
            project=getattr(self, 'project', None)
        )