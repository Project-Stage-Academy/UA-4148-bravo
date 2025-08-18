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

    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        required=True,
        min_value=Decimal("0.01"),
    )

    class Meta:
        model = Subscription
        fields = ["project", "amount"]
        read_only_fields = ["investor"]

    def _effective_current_funding(self, project: Project) -> Decimal:
        agg = project.subscriptions.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        field_val = project.current_funding or Decimal("0.00")
        return max(agg, field_val)

    def validate(self, data):
        project = data.get("project")
        amount = data.get("amount")
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not isinstance(project, Project):
            return data

        investor = getattr(user, "investor", None)
        if not isinstance(investor, Investor):
            raise serializers.ValidationError({"investor": "The requesting user is not an investor."})

        if getattr(project, "startup", None) and getattr(project.startup, "user", None) == getattr(investor, "user", None):
            raise serializers.ValidationError({"non_field_errors": "Investors cannot invest in their own project."})

        current_funding = self._effective_current_funding(project)

        if current_funding >= project.funding_goal:
            raise serializers.ValidationError({"project": "This project is already fully funded."})

        if amount is not None and current_funding + amount > project.funding_goal:
            raise serializers.ValidationError({"amount": "Amount exceeds funding goal — exceeds the remaining funding."})

        data["investor"] = investor
        return data

    def create(self, validated_data):
        amount = validated_data["amount"]
        project = validated_data["project"]

        with transaction.atomic():
            project_locked = Project.objects.select_for_update().get(pk=project.pk)

            current_funding = self._effective_current_funding(project_locked)

            if current_funding >= project_locked.funding_goal:
                raise serializers.ValidationError({"project": "This project is already fully funded."})

            if current_funding + amount > project_locked.funding_goal:
                raise serializers.ValidationError({"amount": "Amount exceeds funding goal — exceeds the remaining funding."})

            subscription = Subscription.objects.create(
                project=project_locked,
                amount=amount,
                investor=validated_data["investor"],
            )

            new_total = Subscription.objects.filter(project=project_locked).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")

            project_locked.current_funding = new_total
            project_locked.save(update_fields=["current_funding"])

        return subscription