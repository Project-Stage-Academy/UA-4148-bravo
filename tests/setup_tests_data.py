import uuid
from decimal import Decimal
from common.enums import Stage, ProjectStatus
from investors.models import Investor
from projects.models import Project, Category
from investments.models import Subscription
from startups.models import Startup, Industry, Location
from users.models import User, UserRole
import os
from dotenv import load_dotenv

load_dotenv()
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")


class TestDataMixin:
    """
    Class for creating and cleaning test data:
    users, investors, startups, projects, subscriptions.
    """

    @classmethod
    def get_or_create_user(cls, email, first_name, last_name):
        user = User.objects.filter(email=email).first()
        if not user:
            role_user, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)
            user = User.objects.create_user(
                email=email,
                password=TEST_USER_PASSWORD,
                first_name=first_name,
                last_name=last_name,
                role=role_user,
                is_active=True
            )
        return user

    @classmethod
    def setup_users(cls):
        cls.user = cls.get_or_create_user("user1@example.com", "Investor", "One")
        cls.user2 = cls.get_or_create_user("user2@example.com", "Investor", "Two")
        cls.investor_user = cls.get_or_create_user("maxinvestor@example.com", "Success", "Investor")
        cls.investor_user2 = cls.get_or_create_user("maxinvestor2@example.com", "Win", "Investor")
        cls.startup_user = cls.get_or_create_user("maxstartup@example.com", "Max", "Startup")

    @classmethod
    def get_or_create_industry(cls, name):
        industry, _ = Industry.objects.get_or_create(name=name)
        return industry

    @classmethod
    def setup_industries(cls):
        cls.industry = cls.get_or_create_industry("Tech")

    @classmethod
    def get_or_create_location(cls, country_code):
        location, _ = Location.objects.get_or_create(country=country_code)
        return location

    @classmethod
    def setup_locations(cls):
        cls.location = cls.get_or_create_location("UA")
        cls.startup_location = cls.get_or_create_location("US")

    @classmethod
    def get_or_create_investor(cls, user, company_name, stage, fund_size):
        email = f"investor_{uuid.uuid4().hex[:6]}@example.com"
        investor, _ = Investor.objects.get_or_create(
            user=user,
            industry=cls.industry,
            location=cls.location,
            company_name=company_name,
            email=email,
            founded_year=2010,
            team_size=5,
            stage=stage,
            fund_size=fund_size
        )
        return investor

    @classmethod
    def setup_investors(cls):
        cls.investor1 = cls.get_or_create_investor(cls.investor_user, "Investor One", Stage.MVP, 1000000.00)
        cls.investor2 = cls.get_or_create_investor(cls.investor_user2, "Investor Two", Stage.LAUNCH, 2000000.00)

    @classmethod
    def get_or_create_startup(cls, user, industry, company_name, location):
        email = f"startup_{uuid.uuid4().hex[:6]}@example.com"
        startup, _ = Startup.objects.get_or_create(
            user=user,
            industry=industry,
            company_name=company_name,
            location=location,
            email=email,
            founded_year=2020,
            team_size=15,
            stage=Stage.MVP
        )
        return startup

    @classmethod
    def setup_startup(cls):
        cls.startup = cls.get_or_create_startup(
            cls.startup_user,
            cls.industry,
            "Test Startup",
            cls.startup_location
        )

    @classmethod
    def get_or_create_category(cls, name="FinTech"):
        category, _ = Category.objects.get_or_create(name=name)
        return category

    @classmethod
    def setup_category(cls):
        cls.category = cls.get_or_create_category()

    @classmethod
    def get_or_create_project(
            cls,
            title="Test Project",
            email=None,
            funding_goal=Decimal("1000000.00"),
            current_funding=Decimal("0.00"),
            startup=None,
            category=None,
            status=ProjectStatus.DRAFT,
            **kwargs
    ):
        """
        Create or get a project with optional custom fields.
        Ensures startup and category are never None.
        """
        if startup is None:
            startup = getattr(cls, "startup", None)
            if startup is None:
                cls.setup_industries()
                cls.setup_locations()
                cls.setup_users()
                startup = cls.get_or_create_startup(
                    cls.startup_user,
                    cls.industry,
                    "Auto Created Startup",
                    cls.startup_location
                )

        if category is None:
            category = getattr(cls, "category", None)
            if category is None:
                category = cls.get_or_create_category()

        if email is None:
            email = f"project_{uuid.uuid4().hex[:6]}@example.com"

        project, _ = Project.objects.get_or_create(
            startup=startup,
            title=title,
            defaults={
                "funding_goal": funding_goal,
                "current_funding": current_funding,
                "category": category,
                "email": email,
                "description": "",
                "duration": 1,
                "status": status,
                **kwargs
            }
        )
        return project

    @classmethod
    def setup_project(cls):
        cls.setup_category()
        cls.project = cls.get_or_create_project()

    @classmethod
    def get_or_create_subscription(cls, investor, project, amount, investment_share=None):
        data = {
            "investor": investor,
            "project": project,
            "amount": Decimal(amount),
        }
        if investment_share is not None:
            data["investment_share"] = Decimal(investment_share)

        subscription, _ = Subscription.objects.get_or_create(**data)
        return subscription

    @staticmethod
    def get_subscription_data(investor, project, amount) -> dict:
        """
        Prepare a dictionary payload representing a subscription, useful for API testing.

        Args:
            investor (Investor or None): Investor instance or None.
            project (Project or None): Project instance or None.
            amount (float): Amount invested.

        Returns:
            dict: Dictionary containing subscription data with IDs for investor and project.
        """
        data = {
            "amount": str(amount)
        }
        if investor is not None:
            data["investor"] = investor.pk
        if project is not None:
            data["project"] = project.pk
        return data

    @classmethod
    def setup_all(cls):
        cls.setup_users()
        cls.setup_industries()
        cls.setup_locations()
        cls.setup_investors()
        cls.setup_startup()
        cls.setup_project()

    @classmethod
    def tear_down(cls):
        Subscription.objects.all().delete()
        Project.objects.all().delete()
        Category.objects.all().delete()
        Startup.objects.all().delete()
        Investor.objects.all().delete()
        Industry.objects.all().delete()
        Location.objects.all().delete()
        User.objects.all().delete()
