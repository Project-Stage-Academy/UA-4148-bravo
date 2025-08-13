from decimal import Decimal

from django.db.models.signals import post_save
from django.test import TestCase
from rest_framework.test import APIClient

from projects.models import Project, Category
from startups.models import Startup, Industry, Location
from startups.signals import update_startup_document
from users.models import UserRole, User


class BaseProjectTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        post_save.disconnect(update_startup_document, sender=Startup)

    @classmethod
    def tearDownClass(cls):
        post_save.connect(update_startup_document, sender=Startup)
        super().tearDownClass()

    def setUp(self):
        """
        Set up test data including users, industry, location, startup,
        project, and investors.
        """
        role = UserRole.objects.get(role=UserRole.Role.USER)
        self.user = User.objects.create_user(
            email='apistartup@example.com',
            password='pass12345',
            first_name='Api',
            last_name='Startup',
            role=role,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.industry = Industry.objects.create(name="Technology")
        self.location = Location.objects.create(country="US")

        self.startup = Startup.objects.create(
            user=self.user,
            industry=self.industry,
            company_name="Test Startup",
            location=self.location,
            email="startup@example.com",
            founded_year=2020,
            team_size=5,
            stage="mvp"
        )

        self.category = Category.objects.create(name="Some Category")
        self.project = Project.objects.create(
            startup=self.startup,
            title="Test Project",
            funding_goal=Decimal("10000.00"),
            current_funding=Decimal("0.00"),
            category=self.category,
            email="project@example.com"
        )
        Project.objects.all().delete()
