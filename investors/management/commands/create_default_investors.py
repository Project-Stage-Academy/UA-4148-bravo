import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from startups.models import Industry, Location
from investors.models import Investor

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Create default investors (idempotent)."

    def handle(self, *args, **options):
        user2 = User.objects.filter(email="user2@example.com").first()
        if not user2:
            self.stdout.write(self.style.ERROR("User user2@example.com does not exist."))
            return

        industry, _ = Industry.objects.get_or_create(name="Finance")
        location, _ = Location.objects.get_or_create(country="US", city="New York", region="NY")

        if Investor.objects.filter(user=user2).exists():
            self.stdout.write(self.style.WARNING("Investor for user2 already exists."))
            return

        investor = Investor.objects.create(
            user=user2,
            company_name="User2 Investment Fund",
            industry=industry,
            location=location,
            stage="mvp",
            fund_size=1000000,
            founded_year=2020,
            email="investor3@example.com",
            description="Leading investment fund focused on technology and finance startups.",
            website="https://user2fund.example.com",
            team_size=15,
        )

        self.stdout.write(self.style.SUCCESS(f"Investor '{investor.company_name}' created successfully."))
        logger.info(f"Investor '{investor.company_name}' created")