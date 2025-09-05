import logging
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from common.enums import Stage
from startups.models import Startup, Industry, Location

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Create default startups (idempotent)."

    def handle(self, *args, **options):
        industries = {
            "Technology": Industry.objects.get_or_create(name="Technology")[0],
            "Healthcare": Industry.objects.get_or_create(name="Healthcare")[0],
            "Finance": Industry.objects.get_or_create(name="Finance")[0],
        }

        locations = {
            "SF": Location.objects.get_or_create(country="US", city="San Francisco", region="CA")[0],
            "NY": Location.objects.get_or_create(country="US", city="New York", region="NY")[0],
            "LDN": Location.objects.get_or_create(country="GB", city="London")[0],
        }
        
        emails_for_startups = ["user1@example.com"]
        
        for email in emails_for_startups:
            user = User.objects.filter(email=email).first()
            if not user:
                self.stdout.write(self.style.ERROR(f"User {email} does not exist."))
                continue

            if Startup.objects.filter(user=user).exists():
                self.stdout.write(self.style.WARNING(f"Startup for {email} already exists."))
                continue

            industry = random.choice(list(industries.values()))
            location = random.choice(list(locations.values()))

            startup = Startup.objects.create(
                user=user,
                company_name=f"{user.first_name}'s Startup",
                industry=industry,
                location=location,
                email=f"{user.email.split('@')[0]}.startup@example.com",
                founded_year=2023,
                team_size=random.randint(3, 15),  
                stage=random.choice([s.value for s in Stage]), 
                description="Default startup for User.",
            )

            self.stdout.write(self.style.SUCCESS(f"Startup '{startup.company_name}' created successfully."))
            logger.info(f"Startup '{startup.company_name}' created")