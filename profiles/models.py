from django.db import models
from django.core.validators import (
    MaxLengthValidator,
    MinValueValidator,
    MaxValueValidator,
    RegexValidator,
)
import datetime
from decimal import Decimal, ROUND_HALF_UP
from validation.validate_email import validate_email_custom


class Country(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[MaxLengthValidator(100)]
    )
    code = models.CharField(
        max_length=3,
        unique=True,
        validators=[
            RegexValidator(regex=r'^[A-Z]{2,3}$', message='Use 2–3 uppercase letters.')
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class City(models.Model):
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name='cities')
    name = models.CharField(
        max_length=100,
        validators=[MaxLengthValidator(100)]
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        validators=[MaxLengthValidator(100)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('country', 'name')

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class Location(models.Model):
    city = models.ForeignKey('City', on_delete=models.CASCADE, related_name='locations')
    address_line = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        validators=[MaxLengthValidator(255)]
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[
            RegexValidator(regex=r'^[\w\s-]{1,20}$', message='Invalid postal code format.')
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        parts = [self.address_line, self.city.name]
        return ", ".join(filter(None, parts))


class Industry(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[MaxLengthValidator(100)]
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Stage(models.TextChoices):
    IDEA = 'idea', 'Idea'
    PROTOTYPE = 'prototype', 'Prototype'
    MVP = 'mvp', 'MVP'
    GROWTH = 'growth', 'Growth'
    SCALE = 'scale', 'Scale'
    ENTERPRISE = 'enterprise', 'Enterprise'


class Company(models.Model):
    company_name = models.CharField(
        max_length=255,
        validators=[MaxLengthValidator(255)]
    )
    description = models.TextField(blank=True, null=True)
    website = models.URLField()
    email = models.EmailField(
        max_length=255,
        validators=[validate_email_custom],
        unique=True
    )
    founded_year = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(datetime.datetime.now().year)
        ]
    )
    team_size = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Startup(Company):
    user = models.OneToOneField(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='startup'
    )
    industry = models.ForeignKey(
        'Industry',
        on_delete=models.PROTECT,
        related_name='startups'
    )
    location = models.ForeignKey(
        'Location',
        on_delete=models.PROTECT,
        related_name='startup_locations'
    )
    startup_logo = models.ImageField(upload_to='startups/logos/')
    social_media = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        validators=[MaxLengthValidator(255)]
    )
    stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.company_name} (Startup, User ID: {self.user_id})"


class Investor(Company):
    user = models.OneToOneField(
        'users.CustomUser',
        on_delete=models.CASCADE,
        related_name='investor'
    )
    industry = models.ForeignKey(
        'Industry',
        on_delete=models.PROTECT,
        related_name='investors'
    )
    location = models.ForeignKey(
        'Location',
        on_delete=models.PROTECT,
        related_name='investor_locations'
    )
    investor_logo = models.ImageField(upload_to='investors/logos/')
    interests = models.TextField(blank=True, null=True)
    fund_size = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)]
    )
    country = models.ForeignKey(
        'Country',
        on_delete=models.PROTECT,
        related_name='investors'
    )
    preferred_stage = models.CharField(
        max_length=20,
        choices=Stage.choices,
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.company_name} (Investor, User ID: {self.user_id})"


class StartupSocialMedia(models.Model):
    startup = models.ForeignKey(
        'Startup',
        on_delete=models.CASCADE,
        related_name='social_links'
    )
    platform = models.CharField(max_length=50)
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.platform} for {self.startup.company_name}"


class Interest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('acknowledged', 'Acknowledged'),
        ('declined', 'Declined')
    ]
    investor = models.ForeignKey('Investor', on_delete=models.CASCADE)
    startup = models.ForeignKey('Startup', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Interest from {self.investor.company_name} in {self.startup.company_name} - Status: {self.status}"


class SavedStartup(models.Model):
    STATUS_CHOICES = [
        ('watching', 'Watching'),
        ('contacted', 'Contacted'),
        ('negotiating', 'Negotiating'),
        ('passed', 'Passed')
    ]
    investor = models.ForeignKey('Investor', on_delete=models.CASCADE)
    startup = models.ForeignKey('Startup', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='watching')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('investor', 'startup')

    def __str__(self):
        return f"{self.investor.company_name} saved {self.startup.company_name} ({self.status})"


class Investment(models.Model):
    investor = models.ForeignKey('Investor', on_delete=models.CASCADE)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.project and self.amount:
            # Calculate the total investment in this project, excluding the current record if it already exists
            other_investments = Investment.objects.filter(project=self.project)
            if self.pk:
                other_investments = other_investments.exclude(pk=self.pk)
            total_amount = other_investments.aggregate(models.Sum('amount'))['amount__sum'] or Decimal('0')
            full_amount = total_amount + self.amount

            if full_amount > 0:
                raw_percent = (self.amount / full_amount) * 100
                self.percent = Decimal(raw_percent).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                self.percent = None
        else:
            self.percent = None

        super().save(*args, **kwargs)

    def __str__(self):
        percent_str = f", {self.percent}%" if self.percent is not None else ""
        return f"Investment of {self.amount} by {self.investor.company_name} in project {self.project} {percent_str}"


class Tag(models.Model):
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
        validators=[MaxLengthValidator(100)]
    )
    tag_type = models.CharField(
        max_length=50,
        choices=TAG_TYPES,
        default='custom',
        validators=[MaxLengthValidator(50)]
    )
    usage_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_tag_type_display()})"


class StartupTag(models.Model):
    startup = models.ForeignKey('Startup', on_delete=models.CASCADE)
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('startup', 'tag')

    def __str__(self):
        return f"Startup: {self.startup}, Tag: {self.tag.name}"


class InvestorTag(models.Model):
    investor = models.ForeignKey('Investor', on_delete=models.CASCADE)
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('investor', 'tag')

    def __str__(self):
        return f"Investor: {self.investor}, Tag: {self.tag.name}"
