from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers
from investments.models import Subscription
from projects.models import Project


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new investment subscription.

    Fields:
        investor (Investor): The investor making the subscription.
        project (Project): The project to invest in.
        amount (Decimal): Investment amount, required and must be >= 0.01.

    Validation:
        - Ensures project exists and is a valid instance.
        - Ensures the requesting user is an investor.
        - Prevents self-investment (investor cannot fund their own startup project).
        - Prevents investments into fully funded projects.
        - Prevents investment amounts that exceed remaining funding.
        - Ensures amount is greater than or equal to 0.01.

    Creation:
        - Uses database transactions with row-level locking to prevent race conditions.
        - Recalculates effective funding using both DB aggregate and project's current_funding to avoid drift.
        - Updates the project's current_funding field after saving the subscription.
    """
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

    class Meta:
        model = Subscription
        fields = ["id", "investor", "project", "amount"]
        extra_kwargs = {"amount": {"required": True}}

    def validate(self, data):
        project = data.get("project")
        investor = data.get("investor")
        amount = data.get("amount")

        if project is None or not isinstance(project, Project):
            raise serializers.ValidationError({"project": "Invalid project."})
        if investor is None or not hasattr(investor, "user"):
            raise serializers.ValidationError({"investor": "Invalid investor."})
        if investor.user == project.startup.user:
            raise serializers.ValidationError(
                {"non_field_errors": ["Startup owners cannot invest in their own project."]}
            )

        aggregated = project.subscriptions.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        effective_current = max(project.current_funding or Decimal("0.00"), aggregated)
        remaining = project.funding_goal - effective_current

        if remaining <= 0:
            raise serializers.ValidationError({"project": "Project is already fully funded."})

        if amount is not None and amount > remaining:
            raise serializers.ValidationError(
                {"amount": "Amount exceeds funding goal — exceeds the remaining funding."}
            )

        return data

    def create(self, validated_data):
        project = validated_data["project"]
        amount = validated_data["amount"]

        with transaction.atomic():
            project_locked = Project.objects.select_for_update().get(pk=project.pk)

            aggregated = project_locked.subscriptions.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
            effective_current = max(project_locked.current_funding or Decimal("0.00"), aggregated)
            remaining = project_locked.funding_goal - effective_current

            if amount > remaining or remaining <= 0:
                raise serializers.ValidationError(
                    {"amount": "Amount exceeds funding goal — exceeds the remaining funding."}
                )

            subscription = Subscription.objects.create(**validated_data)
            project_locked.current_funding = effective_current + amount
            project_locked.save(update_fields=["current_funding"])

        return subscription