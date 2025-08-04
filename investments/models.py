from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Investment(models.Model):
    """
    Represents an investment made by an investor in a specific project.

    Fields:
        investor (ForeignKey): Reference to the Investor making the investment.
        project (ForeignKey): Reference to the Project receiving the investment.
        amount (Decimal): Investment amount. Must be non-negative.
        percent (Decimal): Percentage share of this investment among all investments in the project.
        created_at (DateTime): Timestamp of creation.

    Constraint:
        Investors cannot invest in their own startup's project.
    """
    investor = models.ForeignKey('profiles.Investor', on_delete=models.CASCADE)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE)
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        """ Investors cannot invest in their own startup's project. """
        if self.investor and self.project and self.project.startup.user_id == self.investor.user_id:
            raise ValidationError("Investors cannot invest in their own startup's project.")

    def __str__(self):
        percent_str = f", {self.percent}%" if self.percent is not None else ""
        return f"Investment of {self.amount} by {self.investor.company_name} in project {self.project}{percent_str}"

    class Meta:
        db_table = "investments"
        ordering = ["-created_at"]
        verbose_name = "Investment"
        verbose_name_plural = "Investments"
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gte=0),
                name="amount_non_negative"
            )
        ]
