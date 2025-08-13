from django.core.validators import MinValueValidator
from django.db import models

from common.company import Company
from common.enums import Stage


class Investor(Company):
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='investor'
    )
    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        default=Stage.MVP
    )
    fund_size = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        default=0,
        validators=[MinValueValidator(0)]
    )

    def clean(self):
        """
        Placeholder for future Investor-specific validation logic.
        """
        super().clean()

        if not self.stage:
            self.stage = Stage.MVP

    def __str__(self):
        return f"{self.company_name} (Investor, User ID: {self.user_id})"

    class Meta:
        db_table = "investors"
        ordering = ["company_name"]
        verbose_name = "Investor"
        verbose_name_plural = "Investors"
