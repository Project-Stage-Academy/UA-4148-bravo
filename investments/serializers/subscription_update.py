from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from projects.models import Project
from ..services.investment_share_service import calculate_investment_share
from ..services.subscription_validation_service import validate_subscription_business_rules


class SubscriptionUpdateSerializer():
    """
    Handles subscription updates, ensuring rules are respected.
    """

    def update(self, instance, validated_data):
        new_amount = validated_data.get('amount', instance.amount)

        if 'project' in validated_data and validated_data['project'].pk != instance.project.pk:
            raise serializers.ValidationError({"project": _("Cannot change project of existing subscription.")})

        if 'investor' in validated_data and validated_data['investor'].pk != instance.investor.pk:
            raise serializers.ValidationError({"investor": _("Cannot change investor of existing subscription.")})

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
