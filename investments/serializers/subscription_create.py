from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers

from investments.models import Subscription
from projects.models import Project
from investors.models import Investor


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new investment subscription.

    Fields:
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
    """

    class Meta:
        model = Subscription
        fields = ["id", "investor", "project", "amount"]

    def validate(self, data):
        project = data.get("project")
        investor = data.get("investor")
        amount = data.get("amount")

        if not isinstance(project, Project):
            raise serializers.ValidationError({"project": "Project does not exist."})

        if not getattr(investor, "user", None):
            raise serializers.ValidationError({"investor": "Invalid investor."})

        if amount is None:
            raise serializers.ValidationError({"amount": "This field is required."})

        if amount < Decimal("0.01"):
            raise serializers.ValidationError({"amount": "Amount must be at least 0.01."})

        startup_user = getattr(project.startup, "user", None)
        if startup_user and startup_user == investor.user:
            raise serializers.ValidationError(
                {"non_field_errors": "A startup owner cannot invest in their own project."}
            )

        current_funding = (
            project.subscriptions.aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        if current_funding >= project.funding_goal:
            raise serializers.ValidationError(
                {"project": "This project is already fully funded."}
            )

        if current_funding + amount > project.funding_goal:
            raise serializers.ValidationError(
                {"amount": "Amount exceeds funding goal — exceeds the remaining funding."}
            )

        return data

    def create(self, validated_data):
        amount = validated_data["amount"]
        project = validated_data["project"]

        with transaction.atomic():
            project_locked = Project.objects.select_for_update().get(pk=project.pk)

            subscription = Subscription.objects.create(
                project=project_locked,
                amount=amount,
                investor=validated_data["investor"],
            )

            total = (
                Subscription.objects.filter(project=project_locked).aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

            project_locked.current_funding = total
            project_locked.save(update_fields=["current_funding"])

        return subscription