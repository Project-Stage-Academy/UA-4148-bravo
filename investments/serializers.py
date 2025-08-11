from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Sum
from projects.models import Project
from validation.validate_self_investment import validate_self_investment
from .models import Subscription
from .services.investment_share_service import calculate_investment_share
from decimal import Decimal, InvalidOperation
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist


def get_total_subscribed(project):
    """
    Returns the total amount of funds already subscribed to a given project.
    Returns Decimal('0') if there are no subscriptions.
    """
    total = project.subscriptions.aggregate(total=Sum('amount')).get('total')
    return total if total is not None else Decimal("0")


def validate_project_funding_limit(project, new_amount, current_subscription_amount=Decimal('0.00'),
                                   total_existing=None):
    """
    Check if the new_amount can be added to the total subscribed amount
    without exceeding the project's funding goal.
    Raise serializers.ValidationError if limit exceeded.
    """
    try:
        new_amount = new_amount if isinstance(new_amount, Decimal) else Decimal(str(new_amount))
        if total_existing is not None and not isinstance(total_existing, Decimal):
            total_existing = Decimal(str(total_existing))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise serializers.ValidationError({"amount": _("Invalid numeric value provided.")}) from e

    if total_existing is None:
        total_existing = get_total_subscribed(project)

    if not isinstance(total_existing, Decimal):
        total_existing = Decimal(str(total_existing))

    total_existing -= current_subscription_amount

    if total_existing >= project.funding_goal:
        raise serializers.ValidationError({
            "project": _("Project is fully funded. No further subscriptions allowed.")
        })

    if total_existing + new_amount > project.funding_goal:
        max_allowed = project.funding_goal - total_existing
        max_allowed_str = f"{max_allowed:.2f}"
        raise serializers.ValidationError(
            {"amount": _(f"Subscription amount exceeds funding goal. "
                         f"Maximum allowed: {max_allowed_str}.")}
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Subscription instances with custom validation logic.

    Ensures:
    - Investors cannot invest in their own startup's project.
    - Projects cannot receive investments exceeding their funding goals.
    - Proper calculation of the investment share upon creation.
    """
    amount = serializers.DecimalField(
        max_digits=18,
        decimal_places=2,
        min_value=Decimal("0.01")
    )

    class Meta:
        model = Subscription
        fields = ['id', 'investor', 'project', 'amount', 'investment_share', 'created_at']
        read_only_fields = ['investment_share', 'created_at']

    def _get_field_value(self, data, field_name):
        """
        Returns the field value first from data, if not — from instance,
        if not there — None.
        Args:
            data (dict): The input data to validate, containing 'project', 'investor', and 'amount'.
        """
        if field_name in data:
            return data[field_name]
        if hasattr(self, 'instance') and self.instance is not None:
            return getattr(self.instance, field_name, None)
        return None

    def validate(self, data):
        """
        Perform object-level validation for Subscription creation or update.

        Validates that:
        - The project and investor fields are provided.
        - The investor is not investing in their own project.
        - The new subscription amount does not cause the project's total funding
          to exceed its funding goal.

        Raises:
            serializers.ValidationError: If any validation rule is violated.

        Returns:
            dict: The validated data if all checks pass.
        """
        project = self._get_field_value(data, 'project')
        investor = self._get_field_value(data, 'investor')
        amount = self._get_field_value(data, 'amount')

        errors = {}

        if not project:
            errors['project'] = _("Project is required.")
        if not investor:
            errors['investor'] = _("Investor is required.")

        if errors:
            raise serializers.ValidationError(errors)

        try:
            validate_self_investment(investor, project)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"investor": e.message})

        exclude_amount = Decimal('0.00')
        if self.instance:
            exclude_amount = self.instance.amount
        validate_project_funding_limit(project, amount, current_subscription_amount=exclude_amount)
        return data

    def create(self, validated_data):
        """
        Creates a Subscription instance while ensuring that the total subscribed amount
        does not exceed the project's funding goal. Uses a database transaction with
        row-level locking to prevent race conditions in concurrent requests.

        Args:
            validated_data (dict): Validated data from the serializer.

        Raises:
            serializers.ValidationError: If the new subscription amount exceeds the
                                         remaining funding goal or project is invalid.

        Returns:
            Subscription: The newly created Subscription instance with the calculated
                          investment_share set.
        """
        project = validated_data['project']
        amount = validated_data['amount']

        if not project.pk:
            raise serializers.ValidationError({"project": _("Invalid or unsaved project.")})

        try:
            with transaction.atomic():
                project_locked = Project.objects.select_for_update().get(pk=project.pk)
                total_subscribed = get_total_subscribed(project_locked)
                validate_project_funding_limit(project_locked, amount, total_existing=total_subscribed)
                investment_share = calculate_investment_share(amount, project_locked.funding_goal)
                validated_data['investment_share'] = investment_share
                subscription = Subscription.objects.create(**validated_data)
        except ObjectDoesNotExist:
            raise serializers.ValidationError({"project": _("Project does not exist.")})

        return subscription

    def update_amount(self, instance, validated_data):
        """
        Updates a Subscription instance, ensuring the total subscribed amount
        for the project does not exceed the funding goal. Uses a transaction with
        row-level locking to avoid race conditions.

        Args:
            instance (Subscription): The existing Subscription instance to update.
            validated_data (dict): Validated data from the serializer.

        Raises:
            serializers.ValidationError: If the updated amount exceeds the
                                         project's funding goal.

        Returns:
            Subscription: The updated Subscription instance with recalculated investment_share.
        """
        new_amount = validated_data.get('amount', instance.amount)

        if 'project' in validated_data:
            new_project = validated_data['project']
            if new_project.pk != instance.project.pk:
                raise serializers.ValidationError({"project": _("Cannot change project of existing subscription.")})

        if 'investor' in validated_data and validated_data['investor'].pk != instance.investor.pk:
            raise serializers.ValidationError({"investor": _("Cannot change investor of existing subscription.")})

        with transaction.atomic():
            project = Project.objects.select_for_update().get(pk=instance.project.pk)
            total_subscribed = get_total_subscribed(project)
            validate_project_funding_limit(
                project, new_amount, current_subscription_amount=instance.amount, total_existing=total_subscribed
            )

            investment_share = calculate_investment_share(new_amount, project.funding_goal)
            validated_data['investment_share'] = investment_share

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

        return instance
