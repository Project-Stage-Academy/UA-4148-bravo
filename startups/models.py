from django.db import models

class Startup(models.Model):
    company_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    funding_stage = models.CharField(
        max_length=100,
        choices=[
            ('idea', 'Idea'),
            ('pre-seed', 'Pre-Seed'),
            ('seed', 'Seed'),
            ('series_a', 'Series A'),
            ('series_b', 'Series B'),
            ('growth', 'Growth'),
        ],
        default='idea'
    )
    location = models.CharField(max_length=255, blank=True)
    industries = models.CharField(max_length=255, help_text="Comma-separated list of industries")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name
