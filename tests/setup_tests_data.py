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
    """Create safe test data for users, startups, projects, subscriptions."""

    @classmethod
    def get_or_create_user(cls, email=None, first_name=None, last_name=None):
        """Get or create a user with default USER role."""
        if email is None:
            email = f"user_{uuid.uuid4().hex[:8]}@example.com"

        user = User.objects.filter(email=email).first()
        if not user:
            role_user, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)
            user = User.objects.create_user(
                email=email,
                password=TEST_USER_PASSWORD,
                first_name=first_name or "Test",
                last_name=last_name or "User",
                role=role_user,
                is_active=True
            )
        return user

    @classmethod
    def setup_users(cls):
        """Create standard users for tests."""
        cls.user = cls.get_or_create_user("user1@example.com", "Investor", "One")
        cls.user2 = cls.get_or_create_user("user2@example.com", "Investor", "Two")
        cls.investor_user = cls.get_or_create_user("maxinvestor@example.com", "Success", "Investor")
        cls.investor_user2 = cls.get_or_create_user("maxinvestor2@example.com", "Win", "Investor")
        cls.startup_user = cls.get_or_create_user("maxstartup@example.com", "Max", "Startup")

    @classmethod
    def get_or_create_industry(cls, name):
        """Get or create Industry."""
        industry, _ = Industry.objects.get_or_create(name=name)
        return industry

    @classmethod
    def setup_industries(cls):
        cls.industry = cls.get_or_create_industry("Tech")

    @classmethod
    def get_or_create_location(cls, country_code):
        """Get or create Location."""
        location, _ = Location.objects.get_or_create(country=country_code)
        return location

    @classmethod
    def setup_locations(cls):
        cls.location = cls.get_or_create_location("UA")
        cls.startup_location = cls.get_or_create_location("US")

    @classmethod
    def get_or_create_startup(cls, user, industry, company_name, location):
        """Create or update Startup with sane defaults."""
        email = f"startup_{uuid.uuid4().hex[:8]}@example.com"
        startup, _ = Startup.objects.update_or_create(
            user=user,
            defaults={
                "industry": industry,
                "company_name": company_name,
                "location": location,
                "email": email,
                "founded_year": 2020,
                "team_size": 15,
                "stage": Stage.MVP
            }
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
    def get_or_create_category(cls, name=None):
        """Get or create Project Category."""
        if name is None:
            name = f"Category {uuid.uuid4().hex[:6]}"
        category, _ = Category.objects.get_or_create(name=name)
        return category

    @classmethod
    def setup_category(cls):
        cls.category = cls.get_or_create_category()

    @classmethod
    def get_or_create_project(cls, title=None, email=None, funding_goal=Decimal("1000000.00"),
                              current_funding=Decimal("0.00"), startup=None, category=None,
                              status=ProjectStatus.DRAFT, **kwargs):
        """Create or update Project with sane defaults."""
        if startup is None:
            startup = getattr(cls, "startup", None)
            if startup is None:
                cls.setup_industries()
                cls.setup_locations()
                cls.setup_users()
                startup = cls.get_or_create_startup(cls.startup_user, cls.industry,
                                                   "Auto Created Startup", cls.startup_location)
        if category is None:
            category = getattr(cls, "category", None)
            if category is None:
                category = cls.get_or_create_category()
        if email is None:
            email = f"project_{uuid.uuid4().hex[:8]}@example.com"
        if title is None:
            title = f"Test Project {uuid.uuid4().hex[:6]}"

        project, _ = Project.objects.update_or_create(
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
    def get_or_create_investor(cls, user, company_name, stage, fund_size):
        """Create or update Investor for user with sane defaults."""
        if not hasattr(cls, "industry"):
            cls.setup_industries()
        if not hasattr(cls, "location"):
            cls.setup_locations()

        email = f"investor_{uuid.uuid4().hex[:8]}@example.com"
        investor, _ = Investor.objects.update_or_create(
            user=user,
            defaults={
                "industry": cls.industry,
                "company_name": company_name,
                "location": cls.location,
                "email": email,
                "founded_year": 2015,
                "team_size": 10,
                "stage": stage,
                "fund_size": Decimal(str(fund_size)),
            }
        )
        return investor

    @classmethod
    def setup_investors(cls):
        """Prepare standard investors for tests."""
        cls.investor1 = cls.get_or_create_investor(cls.investor_user, "Investor One", Stage.MVP, 1_000_000)
        cls.investor2 = cls.get_or_create_investor(cls.investor_user2, "Investor Two", Stage.MVP, 2_000_000)
        extra_user = cls.get_or_create_user("investor3@example.com", "Investor", "Three")
        cls.investor3 = cls.get_or_create_investor(extra_user, "Investor Three", Stage.MVP, 500_000)

    @classmethod
    def get_subscription_data(cls, investor, project, amount: Decimal):
        """Return subscription payload for serializer."""
        return {
            "investor": investor.id,
            "project": project.id,
            "amount": str(amount),
        }

    @classmethod
    def setup_project(cls):
        cls.setup_category()
        cls.project = cls.get_or_create_project()

    @classmethod
    def setup_all(cls):
        """Setup all data needed for tests."""
        cls.setup_users()
        cls.setup_industries()
        cls.setup_locations()
        cls.setup_startup()
        cls.setup_category()
        cls.setup_project()
        cls.setup_investors()
