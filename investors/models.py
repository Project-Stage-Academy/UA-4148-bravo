from django.core.validators import MinValueValidator
from django.db import models

from common.company import Company
from common.enums import Stage


class Investor(Company):
    """
    Investor model that inherits from the base Company model.
    Linked to a user via a one-to-one relationship.
    Stores the investor's development stage and fund size.
    """

    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='investor',
        verbose_name="User",
        help_text="The user who owns this investor"
    )
    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        default=Stage.MVP,
        verbose_name="Stage",
        help_text="Current development stage of the investor"
    )
    fund_size = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Fund Size",
        help_text="Size of the investor's fund, must not be negative"
    )

    @property
    def user_id(self):
        return self.user.id if self.user else None

    def __str__(self):
        return f"{self.company_name} (Investor, User ID: {self.user_id})"

    class Meta:
        db_table = "investors"
        ordering = ["company_name"]
        verbose_name = "Investor"
        verbose_name_plural = "Investors"
        indexes = [
            models.Index(fields=['company_name'], name='investor_company_name_idx'),
            models.Index(fields=['stage'], name='investor_stage_idx'),
        ]
