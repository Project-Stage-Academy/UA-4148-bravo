from startups.serializers.startup_full import StartupSerializer
from tests.test_base_case import BaseAPITestCase


class StartupSerializerTests(BaseAPITestCase):
    """
    Tests for StartupSerializer to validate proper serialization and validation
    of Startup data, including required fields, field constraints, and nested data.
    """

    def test_valid_startup_data(self):
        """
        Test that the serializer accepts valid startup data including nested social_links.
        """
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
        """
        Test that the serializer rejects empty or whitespace-only company_name.
        """
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

    def test_missing_email_should_fail(self):
        """
        Test that the serializer rejects empty or missing email field.
        """
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
        self.assertIn('email', serializer.errors)

    def test_team_size_too_small_should_fail(self):
        """
        Test that the serializer rejects team_size values less than 1.
        """
        data = {
            'company_name': 'ValidName',
            'team_size': 0,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020
        }
        serializer = StartupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('team_size', serializer.errors)

    def test_invalid_social_links_should_fail(self):
        """
        Test that the serializer rejects social_links with unsupported platforms or invalid URLs.
        """
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
        self.assertIn('social_links', serializer.errors)

        errors = serializer.errors['social_links']
        self.assertIn("Invalid domain for platform 'linkedin'", errors.get('linkedin', ''))
        self.assertIn("Platform 'unknown' is not supported.", errors.get('unknown', ''))
