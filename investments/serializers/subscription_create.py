from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from projects.models import Project
from utils.get_field_value import get_field_value
from ..models import Subscription
from ..services.investment_share_service import calculate_investment_share
from ..services.subscription_validation_service import validate_subscription_business_rules


class SubscriptionCreateSerializer():
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))

    class Meta:
        model = Subscription
        fields = ['id', 'investor', 'project', 'amount', 'investment_share', 'created_at']
        read_only_fields = ['investment_share', 'created_at']

    def validate(self, data):
        project = get_field_value(data, 'project')
        investor = get_field_value(data, 'investor')
        amount = get_field_value(data, 'amount')
        exclude_amount = Decimal('0.00')

        validate_subscription_business_rules(investor, project, amount, exclude_amount)
        return data

    def create(self, validated_data):
        project = validated_data['project']
        amount = validated_data['amount']

        if not project.pk:
            raise serializers.ValidationError({"project": _("Invalid or unsaved project.")})

        try:
            with transaction.atomic():
                project_locked = Project.objects.select_for_update().get(pk=project.pk)
                validate_subscription_business_rules(validated_data['investor'], project_locked, amount)
                validated_data['investment_share'] = calculate_investment_share(amount, project_locked.funding_goal)
                return Subscription.objects.create(**validated_data)
        except ObjectDoesNotExist:
            raise serializers.ValidationError({"project": _("Project does not exist.")})
