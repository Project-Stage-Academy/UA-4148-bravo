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
    Handles validation for investment amount and project status.
    Uses atomic updates to prevent race conditions.
    """
    class Meta:
        model = Subscription
        fields = ['project', 'amount']
        read_only_fields = ['investor']
 
    def validate(self, data):
        project = data.get('project')
        amount = data.get('amount')
        request = self.context.get('request')
        user = request.user

        try:
            investor = user.investor
        except Investor.DoesNotExist:
            raise serializers.ValidationError({"investor": "The requesting user is not an investor."})

        if project.startup and investor.user == project.startup.user:
            raise serializers.ValidationError({"non_field_errors": "You cannot invest in your own project."})

        current_funding = project.subscriptions.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        if current_funding >= project.funding_goal:
            raise serializers.ValidationError({"project": "This project is already fully funded."})

        if amount is None:
            raise serializers.ValidationError({"amount": "This field is required."})

        if amount <= 0:
            raise serializers.ValidationError({"amount": "Ensure this value is greater than or equal to 0.01."})

        remaining_funding = project.funding_goal - current_funding
        if amount > remaining_funding:
            raise serializers.ValidationError({"amount": "The investment amount exceeds the remaining funding."})

        data['investor'] = investor
        return data
        
    def create(self, validated_data):
        """
        Creates a new subscription instance within a transaction to prevent race conditions.
        """
        amount = serializers.DecimalField(
            max_digits=18,
            decimal_places=2,
            required=True,
            min_value=Decimal("0.01")
        )
        project = validated_data['project']

        with transaction.atomic():

            project_locked = Project.objects.select_for_update().get(pk=project.pk)
            
            if project_locked.current_funding + amount > project_locked.funding_goal:
                raise serializers.ValidationError(
                    {"amount": "The investment amount exceeds the remaining funding."}
                )

            project_locked.current_funding += amount
            project_locked.save()
            
            subscription = Subscription.objects.create(
                project=project_locked,
                amount=amount,
                investor=validated_data['investor']
            )

        return subscription