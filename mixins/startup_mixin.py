from common.enums import Stage
from startups.models import Startup, Industry, Location


class StartupMixin:
    @classmethod
    def create_startup(cls, user, company_name, founded_year, industry, location, **kwargs):
        return Startup.objects.create(
            user=user,
            company_name=company_name,
            founded_year=founded_year,
            industry=industry,
            location=location,
            **kwargs
        )

    @classmethod
    def setup_industry_location_category(cls):
        cls.industry = Industry.objects.create(name="Technology")
        cls.location = Location.objects.create(country="US")

        assert Industry.objects.filter(name=cls.industry.name).exists(), "Industry not created"
        assert Location.objects.filter(country=cls.location.country).exists(), "Location not created"

    @classmethod
    def setup_startup(cls):
        cls.startup = Startup.objects.create(
            user=cls.user_startup,
            industry=cls.industry,
            company_name="Test Startup",
            location=cls.location,
            email="startup@example.com",
            founded_year=2020,
            team_size=15,
            stage=Stage.MVP
        )

        assert Startup.objects.filter(company_name=cls.startup.company_name).exists(), "Startup not created"

    @classmethod
    def setup_all(cls):
        cls.setup_industry_location_category()
        cls.setup_startup()
