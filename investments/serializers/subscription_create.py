from decimal import Decimal
from django.db import transaction
from django.db.models import F
from rest_framework import serializers

from investments.models import Subscription
from projects.models import Project

class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new investment subscription.
    Handles validation for investment amount and project status.
    Uses atomic updates to prevent race conditions.
    """
    class Meta:
        model = Subscription
        fields = ['project', 'amount']

    def validate(self, data):
        """
        Validates the investment amount and the state of the project.
        """
        project = data.get('project')
        amount = data.get('amount')
        user = self.context['request'].user
        investor = getattr(user, 'investor', None)

        if not project:
            raise serializers.ValidationError({"project": "This field is required."})

        if not investor:
             raise serializers.ValidationError({"user": "The requesting user is not an investor."})

        if project.startup and investor.user == project.startup.user:
            raise serializers.ValidationError("You cannot invest in your own project.")

        with transaction.atomic():
            project_locked = Project.objects.select_for_update().get(pk=project.pk)
            
            current_funding = Decimal(str(project_locked.current_funding))
            funding_goal = Decimal(str(project_locked.funding_goal))

            if current_funding >= funding_goal:
                raise serializers.ValidationError("This project is already fully funded.")

            remaining_funding = funding_goal - current_funding
            if amount > remaining_funding:
                raise serializers.ValidationError(
                    f"The investment amount exceeds the remaining funding. Only {remaining_funding} is available."
                )
            
        data['investor'] = investor
        return data
        
    def create(self, validated_data):
        """
        Creates a new subscription and atomically updates the project's funding.
        """
        project = validated_data['project']
        investment_amount = validated_data['investment_amount']
        investor = self.context['request'].user

        with transaction.atomic():
            project.refresh_from_db()

            project.current_funding = F('current_funding') + investment_amount
            project.save()

            project.refresh_from_db()

            subscription = Subscription.objects.create(
                investor=investor,
                **validated_data
            )
        
        return subscription