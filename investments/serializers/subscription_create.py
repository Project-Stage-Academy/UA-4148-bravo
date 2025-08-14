from decimal import Decimal

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from investors.models import Investor
from projects.models import Project
from ..models import Subscription
from ..services.investment_share_service import calculate_investment_share
from ..services.subscription_validation_service import validate_subscription_business_rules


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    investor = serializers.IntegerField()
    project = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))

    class Meta:
        model = Subscription
        fields = ['id', 'investor', 'project', 'amount', 'investment_share', 'created_at']
        read_only_fields = ['investment_share', 'created_at']

    def validate(self, data):
        try:
            investor = Investor.objects.get(pk=data['investor'])
        except Investor.DoesNotExist:
            raise serializers.ValidationError({"investor": _("Investor does not exist.")})

        try:
            project = Project.objects.get(pk=data['project'])
        except Project.DoesNotExist:
            raise serializers.ValidationError({"project": _("Project does not exist.")})

        amount = data['amount']
        exclude_amount = Decimal('0.00')

        validate_subscription_business_rules(investor, project, amount, exclude_amount)
        data['investor'] = investor
        data['project'] = project
        return data

    def create(self, validated_data):
        project = validated_data['project']
        amount = validated_data['amount']

        with transaction.atomic():
            project_locked = Project.objects.select_for_update().get(pk=project.pk)
            validate_subscription_business_rules(validated_data['investor'], project_locked, amount)
            validated_data['investment_share'] = calculate_investment_share(amount, project_locked.funding_goal)
            return Subscription.objects.create(**validated_data)
