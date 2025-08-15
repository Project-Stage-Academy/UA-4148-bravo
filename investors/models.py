from django.core.validators import MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError
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
    
    bookmarks = models.ManyToManyField(
        'startups.Startup',
        through='investors.SavedStartup',
        related_name='bookmarked_by',
        blank=True,
        verbose_name='Bookmarked startups',
        help_text='Startups that this investor has bookmarked.',
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
        
class SavedStartup(models.Model):
    """
    Intermediate model representing a startup saved (bookmarked) by an investor.
    Stores additional metadata such as status, notes, and timestamps.
    """
    investor = models.ForeignKey(
        'investors.Investor',
        on_delete=models.PROTECT,
        related_name='saved_startups',
        db_column='investor_profile_id',
    )
    startup = models.ForeignKey(
        'startups.Startup',
        on_delete=models.PROTECT,
        related_name='saved_by_investors',
        db_column='startup_profile_id',
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ('watching', 'Watching'),
        ('contacted', 'Contacted'),
        ('negotiating', 'Negotiating'),
        ('passed', 'Passed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='watching')
    # щоб не ловити NULL у БД/тестах — краще мати дефолт
    notes = models.TextField(blank=True, default="")   # <-- замість null=True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # нормалізуємо notes
        if self.notes is None:
            self.notes = ""

        # заборона зберегти власний стартап
        inv_user_id = self.investor.user_id if getattr(self, 'investor_id', None) else None
        st_user_id  = self.startup.user_id  if getattr(self, 'startup_id',  None) else None
        if inv_user_id is not None and st_user_id is not None and inv_user_id == st_user_id:
            raise ValidationError({"non_field_errors": ["You cannot save your own startup."]})

    def __str__(self):
        return f"{self.investor} saved {self.startup}"

    class Meta:
        db_table = 'saved_startups'
        constraints = [
            models.UniqueConstraint(fields=['investor', 'startup'], name='uniq_investor_startup')
        ]
        ordering = ['-saved_at']
        verbose_name = 'Saved Startup'
        verbose_name_plural = 'Saved Startups'

