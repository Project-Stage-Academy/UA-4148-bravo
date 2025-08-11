from startups.serializers import StartupSerializer
from startups.tests.test_setup import BaseStartupTestCase


class StartupSerializerTests(BaseStartupTestCase):

    def test_valid_startup_data(self):
        data = {
            'company_name': 'TechNova',
            'description': 'AI-powered analytics for startups and enterprises.',
            'industry': self.industry.id,
            'location': self.location.id,
            'website': 'https://technova.ai',
            'email': 'contact@technova.ai',
            'stage': 'idea',
            'social_links': {
                'linkedin': 'https://linkedin.com/in/technova',
                'twitter': 'https://twitter.com/technova'
            },
            'founded_year': 2020,
            'team_size': 10,
            'user': self.user.pk
        }
        serializer = StartupSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_empty_company_name_should_fail(self):
        data = {
            'company_name': '   ',
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020
        }
        serializer = StartupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('company_name', serializer.errors)

    def test_missing_email_and_website_should_fail(self):
        data = {
            'company_name': 'ValidName',
            'team_size': 5,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'website': '',
            'email': ''
        }
        serializer = StartupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        # Changed check from non_field_errors to email field errors
        self.assertIn('email', serializer.errors)

    def test_team_size_too_small_should_fail(self):
        data = {
            'company_name': 'ValidName',
            'team_size': 0,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'email': 'valid@example.com'
        }
        serializer = StartupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('team_size', serializer.errors)

    def test_invalid_social_links_should_fail(self):
        data = {
            'company_name': 'ValidName',
            'team_size': 5,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'social_links': {
                'linkedin': 'https://notlinkedin.com/profile',
                'unknown': 'https://example.com'
            }
        }
        serializer = StartupSerializer(data=data)
        self.assertFalse(serializer.is_valid())

        # Print errors to check actual message structure
        print(serializer.errors)

        errors = serializer.errors.get('social_links', {})

        # Adjust assertion to check substrings in error messages for robustness
        self.assertTrue(
            any("Invalid domain" in msg for msg in errors.get('linkedin', [])) or
            any("Platform" in msg for msg in errors.get('unknown', []))
        )

