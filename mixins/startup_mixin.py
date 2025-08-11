from common.enums import Stage
from mixins.user_mixin import TEST_USER_PASSWORD
from startups.models import Startup, Industry, Location
from users.models import User, UserRole


class StartupMixin:
    """
    Mixin class providing setup and utility methods for creating Startup, Industry, and Location instances
    used in testing.

    Assumes the consuming test class provides a `user_startup` attribute representing the user for the startup.
    """

    @classmethod
    def create_startup(cls, user, company_name, founded_year, industry, location, **kwargs):
        """
        Create and return a new Startup instance with the provided attributes.

        Args:
            user (User): User instance associated with the startup.
            company_name (str): Name of the startup company.
            founded_year (int): Year the startup was founded.
            industry (Industry): Industry instance associated with the startup.
            location (Location): Location instance associated with the startup.
            **kwargs: Additional fields to pass to Startup creation.

        Returns:
            Startup: Newly created Startup instance.
        """
        return Startup.objects.create(
            user=user,
            company_name=company_name,
            founded_year=founded_year,
            industry=industry,
            location=location,
            **kwargs
        )

    @classmethod
    def setup_industry_location_user(cls):
        """
        Create and assign Industry and Location instances for use in startup creation.

        Sets:
            cls.industry (Industry): Created Industry instance.
            cls.location (Location): Created Location instance.
            cls.user (User): Created User instance.

        Asserts that created instances exist in the database.
        """
        cls.industry = Industry.objects.create(name="Technology")
        cls.location = Location.objects.create(country="US")
        role = UserRole.objects.get(role='user')
        cls.user = User.objects.create_user(
            email='maxstartup@example.com',
            password=TEST_USER_PASSWORD,
            first_name='Max',
            last_name='Startup',
            role=role,
        )

        assert Industry.objects.filter(name=cls.industry.name).exists(), "Industry not created"
        assert Location.objects.filter(country=cls.location.country).exists(), "Location not created"

    @classmethod
    def setup_startup(cls):
        """
        Create and assign a Startup instance linked to the class's `user_startup`, `industry`, and `location`.

        Sets:
            cls.startup (Startup): Created Startup instance.

        Asserts that the startup instance exists in the database.
        """
        cls.startup = Startup.objects.create(
            user=cls.user,
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
        """
        Run all setup steps: create industry, location, and startup instances.
        """
        cls.setup_industry_location_user()
        cls.setup_startup()

    @classmethod
    def tearDownClass(cls):
        """
        Clean up created Startup, Industry, and Location instances after tests.
        Deletes the instances referenced by `cls.startup`, `cls.industry`, and `cls.location`.
        """
        if hasattr(cls, 'startup'):
            Startup.objects.filter(pk=cls.startup.pk).delete()

        if hasattr(cls, 'industry'):
            Industry.objects.filter(pk=cls.industry.pk).delete()

        if hasattr(cls, 'location'):
            Location.objects.filter(pk=cls.location.pk).delete()

        super().tearDownClass()
