from django.core.exceptions import ValidationError
from django.utils import timezone

from common.enums import Stage
from startups.models import Startup
from tests.test_base_case import BaseAPITestCase


class StartupModelCleanTests(BaseAPITestCase):
    """
    Tests for the Startup model's clean() method to ensure proper validation of fields,
    particularly the social_links field for supported platforms and valid URLs.
    """

    def test_valid_clean_should_pass(self):
        """
        All links are valid and from allowed platforms → should not raise ValidationError.
        """
        startup = Startup(
            user=self.user,
            company_name='ValidTech',
            founded_year=2020,
            industry=self.industry,
            location=self.location,
            email='testapistartup@example.com',
            social_links={
                'linkedin': 'https://linkedin.com/in/example',
                'twitter': 'https://twitter.com/example'
            }
        )
        try:
            startup.full_clean()
        except ValidationError as e:
            self.fail(f"ValidationError was raised unexpectedly: {e}")

    def test_invalid_social_links_clean_should_raise(self):
        """
        Test that the clean() method raises ValidationError when social_links contain
        unsupported platforms or invalid domain URLs.
        """
        startup = Startup(
            user=self.user,
            company_name='CleanTech',
            founded_year=2022,
            industry=self.industry,
            location=self.location,
            social_links={
                'linkedin': 'https://notlinkedin.com/profile',
                'unknown': 'https://example.com'
            }
        )
        with self.assertRaises(ValidationError) as context:
            startup.clean()

        errors = context.exception.message_dict

        self.assertIn('linkedin', errors)
        self.assertIn("Invalid domain for platform 'linkedin'", errors['linkedin'][0])

        self.assertIn('unknown', errors)
        self.assertIn("Platform 'unknown' is not supported.", errors['unknown'][0])

    def test_empty_social_links_should_pass(self):
        """
        Empty dict for social_links is allowed.
        """
        startup = Startup(
            user=self.user,
            company_name='EmptySocials',
            founded_year=2021,
            industry=self.industry,
            location=self.location,
            social_links={}
        )
        try:
            startup.clean()
        except ValidationError as e:
            self.fail(f"ValidationError was raised unexpectedly: {e}")

    def test_blank_social_link_value_should_raise(self):
        """
        Blank URL in social_links should raise an error.
        """
        startup = Startup(
            user=self.user,
            company_name='BlankLinkTech',
            founded_year=2022,
            industry=self.industry,
            location=self.location,
            social_links={
                'linkedin': ''
            }
        )
        with self.assertRaises(ValidationError):
            startup.clean()

    def test_invalid_url_format_should_raise(self):
        """
        Non-URL string in social_links should raise an error.
        """
        startup = Startup(
            user=self.user,
            company_name='BadUrlTech',
            founded_year=2022,
            industry=self.industry,
            location=self.location,
            social_links={
                'twitter': 'not_a_url'
            }
        )
        with self.assertRaises(ValidationError):
            startup.clean()

    def test_missing_required_fields_should_raise(self):
        """
        Missing required company_name should raise an error.
        """
        startup = Startup(
            user=self.user,
            founded_year=2022,
            industry=self.industry,
            location=self.location
        )
        with self.assertRaises(ValidationError):
            startup.full_clean()

    def test_description_too_short_should_raise(self):
        """
        Description shorter than 10 chars should raise error (from Company.clean).
        """
        startup = Startup(
            user=self.user,
            company_name='ShortDescTech',
            founded_year=2022,
            industry=self.industry,
            location=self.location,
            description='short',
            social_links={}
        )
        with self.assertRaises(ValidationError) as context:
            startup.clean()

        self.assertIn('description', context.exception.message_dict)
        self.assertIn('at least 10 characters', context.exception.message_dict['description'][0])

    def test_founded_year_out_of_bounds_should_raise(self):
        """Founded year must be between 1900 and current year."""
        current_year = timezone.now().year

        startup_min = Startup(
            user=self.user,
            company_name='TooOldStartup',
            founded_year=1899,
            industry=self.industry,
            location=self.location
        )
        with self.assertRaises(ValidationError) as context_min:
            startup_min.full_clean()
        self.assertIn('founded_year', context_min.exception.message_dict)

        startup_future = Startup(
            user=self.user,
            company_name='FutureStartup',
            founded_year=current_year + 1,
            industry=self.industry,
            location=self.location
        )
        with self.assertRaises(ValidationError) as context_future:
            startup_future.full_clean()
        self.assertIn('founded_year', context_future.exception.message_dict)

    def test_default_stage_is_set_if_missing(self):
        """If stage is not provided, it should default to Stage.IDEA."""
        startup = Startup(
            user=self.user,
            company_name='DefaultStageStartup',
            founded_year=2020,
            industry=self.industry,
            location=self.location
        )
        self.assertEqual(startup.stage, Stage.IDEA)

        startup.save()
        startup.refresh_from_db()
        self.assertEqual(startup.stage, Stage.IDEA)
