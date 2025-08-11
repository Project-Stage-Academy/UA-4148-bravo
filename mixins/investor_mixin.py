from investors.models import Investor
from common.enums import Stage
from decimal import Decimal

from startups.models import Industry, Location


class InvestorMixin:
    @classmethod
    def create_investor(cls, email=None, company_name=None, fund_size="100000.00", user=None, stage=Stage.SEED,
                        **kwargs):
        """
        Create and return a new Investor instance linked to a User and with default attributes.

        Args:
            email (str, optional): Email for the user; required if user is None.
            company_name (str, optional): Name of the investor's company.
            fund_size (str or Decimal, optional): Fund size; default "100000.00".
            user (User, optional): Existing User instance; if None, a new User will be created.
            stage (Stage, optional): Investment stage; default is Stage.SEED.
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
        cls.industry = Industry.objects.create(name="Tech")

    @classmethod
    def setup_location(cls):
        cls.location = Location.objects.create(city="Kyiv", country="Ukraine")

    @classmethod
    def setup_investors(cls):
        cls.investor1 = cls.create_investor("inv1@example.com", "Investor One", "1000000.00", stage=Stage.SEED)
        cls.investor2 = cls.create_investor("inv2@example.com", "Investor Two", "2000000.00", stage=Stage.GROWTH)

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
        assert Investor.objects.filter(
            company_name=cls.startup_investor.company_name).exists(), "Startup Investor not created"

    @classmethod
    def setup_all(cls):
        cls.setup_industry()
        cls.setup_location()
        cls.setup_investors()
