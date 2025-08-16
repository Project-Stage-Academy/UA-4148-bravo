# tests/startups/test_serializer.py
from django.test import TestCase
from startups.serializers.startup_full import StartupSerializer
from tests.startups.test_disable_signal_mixin import DisableElasticsearchSignalsMixin
from tests.test_base_case import BaseAPITestCase


class StartupSerializerTests(DisableElasticsearchSignalsMixin, BaseAPITestCase, TestCase):
    """Tests for StartupSerializer."""

    def test_valid_startup_data(self):
        data = {
            'company_name': 'TechNova',
            'description': 'AI-powered analytics.',
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
            'company_name': ' ',
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020
        }
        serializer = StartupSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('company_name', serializer.errors)




