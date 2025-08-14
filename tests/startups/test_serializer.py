from startups.serializers.startup_full import StartupSerializer
from tests.test_base_case import BaseAPITestCase


class StartupSerializerTests(BaseAPITestCase):
    """
    Tests for StartupSerializer: required fields, constraints, nested social_links.
    """

    def test_valid_startup_data(self):
        """
        Serializer should accept valid payload including social_links.
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
        Empty/whitespace company_name should be rejected.
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

    def test_missing_email_and_website_should_fail(self):
        """
        Both email and website missing/blank should be rejected.
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
        self.assertIn('website', serializer.errors)

    def test_team_size_too_small_should_fail(self):
        """
        team_size < 1 should be rejected.
        """
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
        """
        Unsupported platforms or invalid domains in social_links should be rejected.
        """
        data = {
            'company_name': 'ValidName',
            'team_size': 5,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'email': 'valid@example.com',
            'social_links': {
                'linkedin': 'https://notlinkedin.com/profile',
                'unknown': 'https://example.com'
            }
        }
        serializer = StartupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('social_links', serializer.errors)
        self.assertIn('unknown', serializer.errors['social_links'])


