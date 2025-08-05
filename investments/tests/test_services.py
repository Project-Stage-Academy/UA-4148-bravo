from decimal import Decimal
from django.test import TestCase

from investments.models import Subscription
from investments.services.investment_share_service import recalculate_investment_shares
from users.models import User, UserRole
from profiles.models import Industry, Location, Startup, Investor
from projects.models import Project, Category


class InvestmentShareServiceTest(TestCase):
    """
    Test case for verifying the correct calculation of investment shares
    for subscriptions related to a project.
    """

    def setUp(self):
        """
        Set up test data including users, industry, location, startup,
        project, and investors.
        """
        role_user = UserRole.objects.get(role=UserRole.Role.USER)

        self.user1 = User.objects.create_user(
            email="inv1@example.com",
            password="testpassword123",
            first_name="Investor",
            last_name="One",
            role=role_user
        )
        self.user2 = User.objects.create_user(
            email="inv2@example.com",
            password="testpassword123",
            first_name="Investor",
            last_name="Two",
            role=role_user
        )
        self.user_startup = User.objects.create_user(
            email="startup@example.com",
            password="testpassword123",
            first_name="Startup",
            last_name="User",
            role=role_user
        )

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

        self.investor1 = Investor.objects.create(
            user=self.user1,
            industry=self.industry,
            company_name="Investor One",
            location=self.location,
            email="inv1@example.com",
            founded_year=2010,
            team_size=10,
            stage="mvp",
            fund_size=Decimal("1000000.00")
        )
        self.investor2 = Investor.objects.create(
            user=self.user2,
            industry=self.industry,
            company_name="Investor Two",
            location=self.location,
            email="inv2@example.com",
            founded_year=2015,
            team_size=8,
            stage="growth",
            fund_size=Decimal("2000000.00")
        )

    def test_recalculate_shares(self):
        """
        Test that investment shares are correctly recalculated based on
        the amounts invested by each subscription.
        """
        s1 = Subscription.objects.create(project=self.project, investor=self.investor1, amount=Decimal('100'))
        s2 = Subscription.objects.create(project=self.project, investor=self.investor2, amount=Decimal('300'))

        recalculate_investment_shares(self.project)

        s1.refresh_from_db()
        s2.refresh_from_db()

        self.assertEqual(s1.investment_share, Decimal('25.00'))
        self.assertEqual(s2.investment_share, Decimal('75.00'))
