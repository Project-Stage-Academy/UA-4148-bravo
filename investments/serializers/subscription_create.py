from decimal import Decimal
from django.db import transaction
from rest_framework import serializers

from investments.models import Subscription
from projects.models import Project
from profiles.models import Investor

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
        """
        Validates the investment amount and the state of the project.
        """
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

        if project.current_funding >= project.funding_goal:
            raise serializers.ValidationError({"project": "This project is already fully funded."})
        
        if amount is not None:
            remaining_funding = project.funding_goal - project.current_funding
            if amount > remaining_funding:
                raise serializers.ValidationError({"amount": "The investment amount exceeds the remaining funding."})
        
        data['investor'] = investor
        return data
        
    def create(self, validated_data):
        """
        Creates a new subscription instance within a transaction to prevent race conditions.
        """
        amount = validated_data['amount']
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