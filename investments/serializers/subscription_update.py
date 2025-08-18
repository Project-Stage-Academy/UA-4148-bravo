from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from projects.models import Project
from ..models import Subscription
from ..services.investment_share_service import calculate_investment_share
from ..services.subscription_validation_service import validate_subscription_business_rules


class SubscriptionUpdateSerializer(serializers.ModelSerializer):
    """
    Handles subscription updates, ensuring rules are respected.
    """

    class Meta:
        model = Subscription
        fields = ['investor', 'project', 'amount', 'investment_share', 'created_at']
        read_only_fields = ['investment_share', 'created_at']

    def validate(self, data):
        instance = getattr(self, 'instance', None)

        if instance:
            if 'project' in data and data['project'] != instance.project.id:
                raise serializers.ValidationError({"project": _("Cannot change project of existing subscription.")})

            if 'investor' in data and data['investor'] != instance.investor.id:
                raise serializers.ValidationError({"investor": _("Cannot change investor of existing subscription.")})

        return data

    def update(self, instance, validated_data):
        new_amount = validated_data.get('amount', instance.amount)

        with transaction.atomic():
            project = Project.objects.select_for_update().get(pk=instance.project.pk)
            validate_subscription_business_rules(
                instance.investor, project, new_amount, exclude_amount=instance.amount
            )
            validated_data['investment_share'] = calculate_investment_share(new_amount, project.funding_goal)

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()
            return instance
