from django.core.validators import MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from common.company import Company
from common.enums import Stage
from core import settings


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

    viewed_startups = models.ManyToManyField(
        'startups.Startup',
        through='investors.ViewedStartup',
        related_name='viewed_by',
        blank=True,
        verbose_name='Viewed startups',
        help_text='Startups that this investor recently viewed.',
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
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.notes is None:
            self.notes = ""

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
        indexes = [
            models.Index(fields=['investor', 'startup'], name='saved_investor_startup_idx'),
            models.Index(fields=['status'], name='saved_status_idx'),
            models.Index(fields=['-saved_at'], name='saved_saved_at_desc_idx'),
        ]

class ViewedStartup(models.Model):
    investor = models.ForeignKey(
        'investors.Investor',
        on_delete=models.CASCADE,
        related_name='viewed_startups_links',
        help_text="Investor who viewed the startup"
    )
    startup = models.ForeignKey(
        "startups.Startup",
        on_delete=models.CASCADE,
        related_name="views"
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Startup view history"
        verbose_name_plural = "Startup view histories"
        ordering = ["-viewed_at"]

    def __str__(self):
        return f"{self.investor} viewed {self.startup} at {self.viewed_at}"


class ProjectFollow(models.Model):
    """
    Represents an investor following a specific project.
    
    This model tracks when investors follow projects to receive updates
    and notifications about project progress, milestones, and changes.
    
    Fields:
        investor (ForeignKey): Reference to the Investor following the project.
        project (ForeignKey): Reference to the Project being followed.
        followed_at (DateTime): Timestamp when the follow relationship was created.
        is_active (Boolean): Whether the follow relationship is currently active.
        
    Constraints:
        - Investors cannot follow their own startup's projects.
        - Each investor can follow a project only once (unique constraint).
    """
    
    investor = models.ForeignKey(
        'investors.Investor',
        on_delete=models.CASCADE,
        related_name='followed_projects'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='followers'
    )
    followed_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this follow relationship is currently active"
    )
    
    def clean(self):
        """Custom validation to prevent investors from following their own projects."""
        try:
            if not self.investor_id or not self.project_id:
                return
                
            startup = getattr(self.project, 'startup', None)
            if not startup:
                return
                
            investor_user = getattr(self.investor, 'user', None)
            startup_user = getattr(startup, 'user', None)
            
            if (investor_user and startup_user and 
                getattr(investor_user, 'pk', None) == getattr(startup_user, 'pk', None)):
                raise ValidationError({
                    "non_field_errors": ["Investors cannot follow their own startup's projects."]
                })
        except (AttributeError, self.DoesNotExist):
            pass
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.investor.company_name} follows {self.project.title}"
    
    class Meta:
        db_table = "project_follows"
        ordering = ["-followed_at"]
        verbose_name = "Project Follow"
        verbose_name_plural = "Project Follows"
        constraints = [
            models.UniqueConstraint(
                fields=["investor", "project"],
                name="unique_investor_project_follow"
            ),
        ]
        indexes = [
            models.Index(fields=["investor"], name="idx_project_follow_investor"),
            models.Index(fields=["project"], name="idx_project_follow_project"),
            models.Index(fields=["followed_at"], name="idx_project_follow_followed_at"),
            models.Index(fields=["is_active"], name="idx_project_follow_is_active"),
        ]
