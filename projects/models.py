from django.db import models
from startups.models import Startup

class Project(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=100,
        choices=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('archived', 'Archived'),
        ],
        default='draft'
    )
    required_amount = models.DecimalField(max_digits=12, decimal_places=2)
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='projects')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
