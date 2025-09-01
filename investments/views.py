import logging
from decimal import Decimal, ROUND_HALF_UP

from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status

from users.cookie_jwt import CookieJWTAuthentication
from users.permissions import IsAuthenticatedInvestor403  # always 403 for any unauthorized access
from investments.models import Subscription
from investments.serializers import SubscriptionCreateSerializer
from projects.models import Project

logger = logging.getLogger(__name__)


class SubscriptionCreateView(CreateAPIView):
    """
    Create an investment subscription for a project.

    Security:
      - Only authenticated users with an Investor profile are allowed.
      - Any unauthorized access (unauthenticated or not an investor) → 403 Forbidden.

    Notes:
      - Business validation & atomic updates are handled inside the serializer.
      - We DO NOT manually change project's current_funding here to avoid double-counting.
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionCreateSerializer
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedInvestor403]

    def _get_project_or_404_payload(self):
        """
        Resolve project from URL.
        Returns (project, None) if found, or (None, Response(..., 404)) with a
        custom JSON message required by tests.
        """
        project_id = self.kwargs.get("project_id")
        try:
            return Project.objects.get(pk=project_id), None
        except Project.DoesNotExist:
            return None, Response(
                {"project": "Project does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def create(self, request, *args, **kwargs):
        """
        1) Resolve project (custom 404 response if not found).
        2) Validate request payload via serializer (pass project in context).
        3) Save subscription – serializer performs atomic logic and project update.
        4) Refresh project from DB and return funding status.
        """
        project, not_found_response = self._get_project_or_404_payload()
        if not_found_response:
            return not_found_response

        serializer = self.get_serializer(
            data=request.data,
            context={"request": request, "project": project},
        )
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
        except Exception:
            logger.exception(
                "Failed to create subscription for user %s",
                getattr(request.user, "id", None),
            )
            return Response(
                {"detail": "Failed to create subscription. Please try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Refresh project to get the updated funding values
        project.refresh_from_db(fields=["current_funding", "funding_goal"])

        remaining = (project.funding_goal - project.current_funding)
        remaining = (remaining.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                     if isinstance(remaining, Decimal)
                     else Decimal(remaining).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        project_status = "Fully funded" if remaining <= 0 else "Partially funded"

        logger.info(
            "Subscription created successfully for project %s by user %s",
            project.id,
            request.user.id,
        )

        return Response(
            {
                "message": "Subscription created successfully.",
                "subscription": SubscriptionCreateSerializer(
                    serializer.instance, context={"request": request}
                ).data,
                "remaining_funding": remaining,  # Decimal, not string
                "project_status": project_status,
            },
            status=status.HTTP_201_CREATED,
        )

    def perform_create(self, serializer):
        """
        Save subscription with bound investor and project.
        The serializer itself handles validation, limits, and safe project update.
        """
        project, _ = self._get_project_or_404_payload()
        serializer.save(
            investor=self.request.user.investor,
            project=project,
        )
