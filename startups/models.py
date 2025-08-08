from django.db import models

class Industry(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Location(models.Model):
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100)

    class Meta:
        unique_together = ('city', 'state', 'country')

    def __str__(self):
        if self.state:
            return f"{self.city}, {self.state}, {self.country}"
        return f"{self.city}, {self.country}"

class Startup(models.Model):
    company_name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='startups')
    industries = models.ManyToManyField(Industry, related_name='startups')
    funding_stage = models.CharField(max_length=50)

    def __str__(self):
        return self.company_name