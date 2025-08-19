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
        - Recalculates funding based on committed subscriptions at creation time.
        - Updates the project's current_funding field after saving the subscription.
    """

    class Meta:
        model = Subscription
        fields = ["id", "investor", "project", "amount"]

    def validate(self, data):
        project = data.get("project")
        investor = data.get("investor")
        amount = data.get("amount")

        if project is None or not isinstance(project, Project):
            raise serializers.ValidationError({"project": "Invalid project."})

        if investor is None or not hasattr(investor, "user"):
            raise serializers.ValidationError({"investor": "Invalid investor."})

        if amount is not None and amount < Decimal("0.01"):
            raise serializers.ValidationError({"amount": "Investment amount must be at least 0.01."})

        if investor.user == project.startup.user:
            raise serializers.ValidationError({"non_field_errors": ["Startup owners cannot invest in their own project."]})

        return data

    def create(self, validated_data):
        project = validated_data["project"]
        amount = validated_data["amount"]

        with transaction.atomic():
            project_locked = Project.objects.select_for_update().get(pk=project.pk)

            current_funding = project_locked.subscriptions.aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")

            remaining = project_locked.funding_goal - current_funding

            if remaining <= 0:
                raise serializers.ValidationError({"project": "Project is already fully funded."})

            if amount > remaining:
                raise serializers.ValidationError(
                    {"amount": "Amount exceeds funding goal — exceeds the remaining funding."}
                )

            subscription = Subscription.objects.create(**validated_data)
            new_total = project_locked.subscriptions.aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")

            project_locked.current_funding = new_total
            project_locked.save(update_fields=["current_funding"])

        return subscription
