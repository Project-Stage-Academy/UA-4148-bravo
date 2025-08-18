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
        min_value=Decimal("0.01")
    )

    class Meta:
        model = Subscription
        fields = ['project', 'amount']
        read_only_fields = ['investor']

    def validate(self, data):
        project = data.get('project')
        amount = data.get('amount')
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if not isinstance(project, Project):
            raise serializers.ValidationError({"project": "Project does not exist"})

        investor = getattr(user, 'investor', None)
        if not isinstance(investor, Investor):
            raise serializers.ValidationError({"investor": "The requesting user is not an investor."})

        if getattr(project, 'startup', None) and getattr(project.startup, 'user', None) == getattr(investor, 'user', None):
            raise serializers.ValidationError({"non_field_errors": "Investors cannot invest in their own project."})

        current_funding = project.subscriptions.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        if current_funding >= project.funding_goal:
            raise serializers.ValidationError({"project": "This project is fully funded."})

        if amount is not None and amount < Decimal("0.01"):
            raise serializers.ValidationError({"amount": "Ensure this value is greater than or equal to 0.01."})

        remaining_funding = project.funding_goal - current_funding
        if amount and amount > remaining_funding:
            raise serializers.ValidationError({"amount": "Amount exceeds funding goal."})

        data['investor'] = investor
        return data

    def create(self, validated_data):
        amount = validated_data['amount']
        project = validated_data['project']

        with transaction.atomic():
            project_locked = Project.objects.select_for_update().get(pk=project.pk)

            current_funding = project_locked.subscriptions.aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0.00")

            if current_funding + amount > project_locked.funding_goal:
                raise serializers.ValidationError(
                    {"amount": "Amount exceeds funding goal."}
                )

            subscription = Subscription.objects.create(
                project=project_locked,
                amount=amount,
                investor=validated_data['investor']
            )

        return subscription