from django.core.exceptions import ValidationError

from startups.models import Startup
from startups.tests.test_setup import BaseStartupTestCase


class StartupModelCleanTests(BaseStartupTestCase):

    def test_invalid_social_links_clean_should_raise(self):
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
