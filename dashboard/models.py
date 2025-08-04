from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models


class InvestorStartupConnection(models.Model):
    """
    Represents a relationship between an investor and a startup.

    This covers different types of relationships such as:
    - Interest: Active investment interest or ongoing negotiations.
    - Saved: Bookmark/watchlist status.

    The 'relation_type' field distinguishes these.

    Fields:
    - investor
    - startup
    - relation_type (interest, saved, etc.)
    - status (varies based on relation_type)
    - notes
    - timestamps
    """

    RELATION_TYPE_INTEREST = 'interest'
    RELATION_TYPE_SAVED = 'saved'

    RELATION_TYPE_CHOICES = [
        (RELATION_TYPE_INTEREST, 'Interest'),
        (RELATION_TYPE_SAVED, 'Saved'),
    ]

    STATUS_CHOICES = {
        RELATION_TYPE_INTEREST: [
            ('pending', 'Pending'),
            ('acknowledged', 'Acknowledged'),
            ('declined', 'Declined'),
        ],
        RELATION_TYPE_SAVED: [
            ('watching', 'Watching'),
            ('contacted', 'Contacted'),
            ('negotiating', 'Negotiating'),
            ('passed', 'Passed'),
        ],
    }

    investor = models.ForeignKey('profiles.Investor', on_delete=models.CASCADE)
    startup = models.ForeignKey('profiles.Startup', on_delete=models.CASCADE)
    relation_type = models.CharField(max_length=20, choices=RELATION_TYPE_CHOICES)
    status = models.CharField(max_length=20)
    notes = models.TextField(max_length=2000, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Validates the InvestorStartupConnection instance.

        Raises:
            ValidationError:
                - If investor relates to their own startup.
                - If the status is invalid for the relation_type.
                - If status update violates rules (e.g., changing acknowledged/declined interest status).
        """
        errors = {}

        if self.investor.user_id == self.startup.user_id:
            errors['startup'] = "Investor cannot relate to their own startup."

        valid_statuses = dict(self.STATUS_CHOICES.get(self.relation_type, []))
        if self.status not in valid_statuses:
            errors['status'] = f"Invalid status '{self.status}' for relation type '{self.relation_type}'."

        if self.pk:
            old_status = InvestorStartupConnection.objects.filter(pk=self.pk).values_list('status', flat=True).first()
            if self.relation_type == self.RELATION_TYPE_INTEREST:
                if old_status in ['acknowledged', 'declined'] and self.status != old_status:
                    errors['status'] = f"Cannot change status once it is '{old_status}'."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.get_relation_type_display()} from {self.investor.company_name} to {self.startup.company_name} - Status: {self.status}"

    class Meta:
        db_table = "investor_startup_connections"
        constraints = [
            models.UniqueConstraint(
                fields=['investor', 'startup', 'relation_type'],
                name='unique_investor_startup_connection'
            )
        ]
        ordering = ['-created_at']
        verbose_name = "Investor Startup Connection"
        verbose_name_plural = "Investor Startup Connections"


class Tag(models.Model):
    """
    Represents a tag that can be associated with startups, projects, or other entities.

    Tags help in categorizing and filtering data. Each tag has a type (e.g., industry, technology)
    and a usage count to indicate how often it has been applied.
    """
    TAG_TYPES = [
        ('industry', 'Industry'),
        ('technology', 'Technology'),
        ('stage', 'Stage'),
        ('topic', 'Topic'),
        ('custom', 'Custom'),
    ]

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the tag. Must be unique."
    )
    tag_type = models.CharField(
        max_length=50,
        choices=TAG_TYPES,
        default='custom',
        help_text="The category/type of the tag."
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="The number of times this tag has been used."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_tag_type_display()})"

    class Meta:
        db_table = 'tags'
        ordering = ['tag_type', 'name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['tag_type']),
        ]


class TaggedEntity(models.Model):
    """
    Generic tagging model that assigns a Tag to any entity (Startup, Investor, etc.)
    """
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'tagged_entities'
        constraints = [
            models.UniqueConstraint(
                fields=['tag', 'content_type', 'object_id'],
                name='unique_tag_per_entity'
            )
        ]
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['tag']),
        ]

    def __str__(self):
        return f"{self.tag.name} tagged to {self.content_object}"
