import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from startups.models import Startup
from projects.models import Category, Project

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Create default projects (idempotent)."

    def handle(self, *args, **options):
        category, _ = Category.objects.get_or_create(
            name="AI",
            defaults={"description": "Artificial Intelligence related projects."}
        )

        user1 = User.objects.filter(email="user1@example.com").first()
        if not user1:
            self.stdout.write(self.style.ERROR("User user1@example.com does not exist."))
            return

        startup = Startup.objects.filter(user=user1).first()
        if not startup:
            self.stdout.write(self.style.ERROR("Startup for user1 does not exist."))
            return

        if Project.objects.filter(title="AI Project", startup=startup).exists():
            self.stdout.write(self.style.WARNING("AI Project already exists for user1's startup."))
            return

        project = Project.objects.create(
            startup=startup,
            title="AI Project",
            description="Demo project for User1 startup.",
            status="draft",
            duration=180,
            funding_goal=Decimal("100000.00"),
            current_funding=Decimal("0.00"),
            category=category,
            website="https://user1-startup-project.com",
            email="ai.project@user1-startup.com",
            has_patents=False,
            is_participant=True,
            is_active=True,
        )

        self.stdout.write(self.style.SUCCESS(f"Project '{project.title}' created successfully."))
        logger.info(f"Project '{project.title}' created")