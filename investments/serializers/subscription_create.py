from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from investors.models import Investor
from projects.models import Project
from investments.models import Subscription
from ..services.subscription_validation_service import validate_subscription_business_rules
from ..services.investment_share_service import (
    update_project_investment_shares_if_needed,
    calculate_investment_share,
)


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating subscriptions.

    Validation:
        - Ensures investor exists and is valid.
        - Prevents self-investment (investor cannot fund their own startup project).
        - Prevents investments into fully funded projects.
        - Prevents amounts exceeding the remaining funding.
        - Ensures amount >= 0.01.

    Creation:
        - Uses DB transaction with row locking to prevent race conditions.
        - Runs central business rules validation.
        - Recalculates investment shares and updates project's funding.
    """

    investor = serializers.PrimaryKeyRelatedField(queryset=Investor.objects.all())
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(),
        error_messages={
            "does_not_exist": _("Project does not exist or is not available for investment.")
        },
    )
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))

    class Meta:
        model = Subscription
        fields = ["id", "investor", "project", "amount"]
        extra_kwargs = {"amount": {"required": True}}

    def validate(self, data):
        project = data.get("project")
        investor = data.get("investor")
        amount = data.get("amount")

        # Self-investment check
        startup = getattr(project, "startup", None)
        if startup and investor and getattr(investor, "user", None) and getattr(startup, "user", None):
            if investor.user.pk == startup.user.pk:
                raise serializers.ValidationError(
                    {"non_field_errors": ["Startup owners cannot invest in their own project."]}
                )

        # Funding checks
        aggregated = project.subscriptions.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        effective_current = max(project.current_funding or Decimal("0.00"), aggregated)

        if effective_current >= project.funding_goal:
            raise serializers.ValidationError({"project": "Project is fully funded."})

        remaining = project.funding_goal - effective_current
        if amount and amount > remaining:
            raise serializers.ValidationError(
                {"amount": f"Amount exceeds funding goal — max allowed: {remaining:.2f}"}
            )

        return data

    def create(self, validated_data):
        project = validated_data["project"]
        investor = validated_data["investor"]
        amount = validated_data["amount"]

        with transaction.atomic():
            project_locked = Project.objects.select_for_update().get(pk=project.pk)

            # Central business rules
            validate_subscription_business_rules(investor, project_locked, amount)

            subscription = Subscription.objects.create(**validated_data)

            # Calculate and save share
            subscription.investment_share = calculate_investment_share(
                subscription.amount, project_locked.funding_goal
            )
            subscription.save(update_fields=["investment_share"])

            # Update funding and recalc shares
            aggregated = project_locked.subscriptions.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            project_locked.current_funding = aggregated
            project_locked.save(update_fields=["current_funding"])

            update_project_investment_shares_if_needed(project_locked)

            return subscription
