from django.db import models
from django.db.models import UniqueConstraint, F

class Industry(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Location(models.Model):
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100)

    class Meta:
        constraints = [
            UniqueConstraint(
                F('city'),
                F('state'),
                F('country'),
                name='unique_location',
                violation_error_message='This location already exists.'
            )
        ]

    def __str__(self):
        city_str = self.city if self.city else 'Unknown City'
        country_str = self.country if self.country else 'Unknown Country'

        if self.state:
            return f"{city_str}, {self.state}, {country_str}"
        return f"{city_str}, {country_str}"

class Startup(models.Model):
    company_name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.ForeignKey(Location, on_delete=models.PROTECT, null=True, related_name='startups')
    industries = models.ManyToManyField(Industry, related_name='startups')
    funding_stage = models.CharField(max_length=50)

    def __str__(self):
        return self.company_name