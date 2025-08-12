from django.test import TestCase
from decimal import Decimal
from users.models import User, UserRole
from investors.models import Investor
from startups.models import Startup, Industry, Location
from projects.models import Project, Category
from django.db.models.signals import post_save
from startups.signals import update_startup_document
from rest_framework.test import APIClient


class BaseInvestmentTestCase(TestCase):
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
        self.role_user = UserRole.objects.get(role=UserRole.Role.USER)

        self.user1 = self._create_user("inv1@example.com", "Investor", "One")
        self.user2 = self._create_user("inv2@example.com", "Investor", "Two")
        self.user_startup = self._create_user("startup@example.com", "Startup", "User")

        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

        self.industry = Industry.objects.create(name="Technology")
        self.location = Location.objects.create(country="US")

        self.startup = Startup.objects.create(
            user=self.user_startup,
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

        self.investor1 = self._create_investor(self.user1, "Investor One", Decimal("1000000.00"))
        self.investor2 = self._create_investor(self.user2, "Investor Two", Decimal("2000000.00"))

    def _create_user(self, email, first_name, last_name):
        return User.objects.create_user(
            email=email,
            password="testpassword123",
            first_name=first_name,
            last_name=last_name,
            role=self.role_user
        )

    def _create_investor(self, user, company_name, fund_size):
        return Investor.objects.create(
            user=user,
            industry=self.industry,
            company_name=company_name,
            location=self.location,
            email=user.email,
            founded_year=2010,
            team_size=5,
            stage="mvp",
            fund_size=fund_size
        )
