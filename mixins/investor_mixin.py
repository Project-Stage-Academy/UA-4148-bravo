from investors.models import Investor
from common.enums import Stage
from decimal import Decimal
from startups.models import Industry, Location


class InvestorMixin:
    """
    Mixin class providing reusable setup and utility methods for creating Investor
    instances and related objects for testing purposes.

    This mixin handles:
    - Creating Industry and Location instances used for Investors.
    - Creating Investor instances linked to Users with default or custom attributes.
    - Cleaning up created objects after tests.

    Requires that the consuming test class provide a `create_user` method
    and `user_startup` attribute for user creation and linking.
    """

    @classmethod
    def create_investor(cls, email=None, company_name=None, fund_size="100000.00", user=None, stage=Stage.MVP,
                        **kwargs):
        """
        Create and return a new Investor instance linked to a User.

        If a User instance is not provided, creates one using `cls.create_user`.

        Args:
            email (str, optional): Email for the user; required if user is None.
            company_name (str, optional): Name of the investor's company.
            fund_size (str or Decimal, optional): Fund size; defaults to "100000.00".
            user (User, optional): Existing User instance; if None, a new User will be created.
            stage (Stage, optional): Investment stage; defaults to Stage.SEED.
            **kwargs: Additional fields to pass to Investor creation.

        Returns:
            Investor: Newly created Investor instance.
        """
        if not user:
            user = cls.create_user(email, company_name, company_name)
        return Investor.objects.create(
            user=user,
            industry=cls.industry,
            location=cls.location,
            company_name=company_name,
            email=user.email,
            founded_year=2010,
            team_size=5,
            stage=stage,
            fund_size=Decimal(fund_size),
            **kwargs
        )

    @classmethod
    def setup_industry(cls):
        """
        Create and assign an Industry instance to `cls.industry` for testing use.
        """
        cls.industry = Industry.objects.create(name="Tech")

    @classmethod
    def setup_location(cls):
        """
        Create and assign a Location instance to `cls.location` for testing use.
        """
        cls.location = Location.objects.create(city="Kyiv", country="UA")

    @classmethod
    def setup_investors(cls):
        """
        Create multiple Investor instances with predefined attributes
        and assign them to class attributes for test access.

        Also creates a startup-linked investor using an existing startup user.
        """
        cls.investor1 = cls.create_investor("inv1@example.com", "Investor One", "1000000.00", stage=Stage.MVP)
        cls.investor2 = cls.create_investor("inv2@example.com", "Investor Two", "2000000.00", stage=Stage.LAUNCH)

        cls.startup_investor = Investor.objects.create(
            user=cls.user_startup,
            industry=cls.industry,
            location=cls.location,
            company_name="Startup VC",
            email=cls.user_startup.email,
            founded_year=2010,
            team_size=300,
            stage=Stage.SCALE,
            fund_size=Decimal("10000.00")
        )

        assert Investor.objects.filter(company_name=cls.investor1.company_name).exists(), "Investor1 not created"
        assert Investor.objects.filter(company_name=cls.investor2.company_name).exists(), "Investor2 not created"
        assert Investor.objects.filter(company_name=cls.startup_investor.company_name).exists(), "Startup Investor not created"

    @classmethod
    def setup_all(cls):
        """
        Run all setup steps: industry, location, and investors.
        """
        cls.setup_industry()
        cls.setup_location()
        cls.setup_investors()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up all created database objects after tests finish.

        Deletes created Investor instances, Industry, Location, and the startup user.
        """
        investor_names = [
            getattr(cls, 'investor1', None).company_name if hasattr(cls, 'investor1') else None,
            getattr(cls, 'investor2', None).company_name if hasattr(cls, 'investor2') else None,
            getattr(cls, 'startup_investor', None).company_name if hasattr(cls, 'startup_investor') else None,
        ]
        Investor.objects.filter(company_name__in=[name for name in investor_names if name]).delete()

        if hasattr(cls, 'industry'):
            cls.industry.delete()

        if hasattr(cls, 'location'):
            cls.location.delete()

        if hasattr(cls, 'user_startup'):
            cls.user_startup.delete()

        super().tearDownClass()
