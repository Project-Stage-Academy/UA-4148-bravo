from enum import unique, Enum
from django.db import models

from users.models import User


@unique
class Stage(str, Enum):
    IDEA = 'idea'
    PROTOTYPE = 'prototype'
    MVP = 'mvp'
    GROWTH = 'growth'
    SCALE = 'scale'

    @classmethod
    def choices(cls):
        return [(key.value, key.value.capitalize()) for key in cls]


class BaseProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class StartUpProfile(BaseProfile):
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    founded_year = models.PositiveIntegerField(blank=True, null=True)
    team_size = models.PositiveIntegerField(blank=True, null=True)
    social_media = models.CharField(max_length=255, blank=True, null=True)
    stage = models.CharField(max_length=20, choices=Stage.choices(), blank=True, null=True)

    def __str__(self):
        return f"{self.company_name} (StartUp, User ID: {self.user_id})"


class InvestorProfile(BaseProfile):
    interests = models.TextField(blank=True, null=True)
    fund_size = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    preferred_stage = models.CharField(max_length=20, choices=Stage.choices(), blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.company_name} (Investor, User ID: {self.user_id})"
