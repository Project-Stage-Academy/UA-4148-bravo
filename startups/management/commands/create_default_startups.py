import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
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

        user1 = User.objects.filter(email="user1@example.com").first()
        if not user1:
            self.stdout.write(self.style.ERROR("User user1@example.com does not exist."))
            return

        if Startup.objects.filter(user=user1).exists():
            self.stdout.write(self.style.WARNING("Startup for user1 already exists."))
            return

        startup = Startup.objects.create(
            user=user1,
            company_name="User1 Tech Startup",
            industry=industries["Technology"],
            location=locations["SF"],
            email="user1.startup@example.com",
            founded_year=2023,
            team_size=5,
            stage="idea",
            description="Default startup for User1.",
        )

        self.stdout.write(self.style.SUCCESS(f"Startup '{startup.company_name}' created successfully."))
        logger.info(f"Startup '{startup.company_name}' created")