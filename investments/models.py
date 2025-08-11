from decimal import Decimal

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from validation.validate_self_investment import validate_self_investment


class Subscription(models.Model):
    """
    Represents an investment made by an investor in a specific project.

    Fields:
        investor (ForeignKey): Reference to the Investor making the investment.
        project (ForeignKey): Reference to the Project receiving the investment.
        amount (Decimal): Investment amount. Must be non-negative.
        investment_share (Decimal): The share (percentage) of the total investments
            this subscription represents in the project. Calculated automatically.
        created_at (DateTime): Timestamp when the subscription was created.

    Constraints:
        - Investors cannot invest in their own startup's project.
        - Each investor can have only one subscription per project (unique constraint).
    """

    investor = models.ForeignKey(
        'investors.Investor',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        default=Decimal("0.01")
    )
    investment_share = models.DecimalField(
        editable=False,
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.00), MaxValueValidator(100.00)],
        default=Decimal('0.00')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """ Custom validation to prevent investors from investing in their own projects. """
        validate_self_investment(self.investor, self.project)

    def __str__(self):
        percent_str = f", {self.investment_share}%" if self.investment_share is not None else ""
        return f"Investment of {self.amount} by {self.investor.company_name} in project {self.project}{percent_str}"

    class Meta:
        db_table = "subscriptions"
        ordering = ["-created_at"]
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        constraints = [
            models.UniqueConstraint(
                fields=["investor", "project"],
                name="unique_investor_project"
            ),
        ]
        indexes = [
            models.Index(fields=["project"], name="idx_subscription_project"),
            models.Index(fields=["investor"], name="idx_subscription_investor"),
        ]
