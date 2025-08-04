from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from decimal import Decimal, ROUND_HALF_UP
from django.db import models

from investments.models import Investment


@receiver([post_save, post_delete], sender=Investment)
def update_investment_percents(instance):
    project = instance.project
    investments = Investment.objects.filter(project=project)
    total = investments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
    for investment in investments:
        if total > 0:
            investment.percent = (investment.amount / total * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            investment.percent = Decimal('0.00')
        investment.save(update_fields=['percent'])
