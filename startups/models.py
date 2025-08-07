from django.db import models

class Industry(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Startup(models.Model):
    company_name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    industries = models.ManyToManyField(Industry, related_name='startups')
    funding_stage = models.CharField(max_length=50)

    def __str__(self):
        return self.company_name