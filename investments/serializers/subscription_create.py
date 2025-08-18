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

        if project.current_funding >= project.funding_goal:
            raise serializers.ValidationError({"project": "This project is already fully funded."})

        if amount and project.current_funding + amount > project.funding_goal:
            raise serializers.ValidationError({"amount": "The investment amount exceeds the remaining funding."})

        data["investor"] = investor
        return data

    def create(self, validated_data):
        amount = validated_data['amount']
        project = validated_data['project']

        with transaction.atomic():
            project = Project.objects.select_for_update().get(pk=project.pk)

            if project.current_funding >= project.funding_goal:
                raise serializers.ValidationError({"project": "This project is already fully funded."})

            if project.current_funding + amount > project.funding_goal:
                raise serializers.ValidationError({"amount": "The investment amount exceeds the remaining funding."})

            subscription = Subscription.objects.create(
                project=project,
                amount=amount,
                investor=validated_data["investor"]
            )
            
            project.current_funding += amount
            project.save(update_fields=["current_funding"])

        return subscription