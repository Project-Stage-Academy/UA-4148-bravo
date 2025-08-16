from rest_framework import serializers
from startups.models import Startup
from tests.test_base_case import BaseAPITestCase

class StartupSerializerTest(BaseAPITestCase):
    """ Tests for Startup serializer validation. """

    def test_serializer_valid_data(self):
        """ Serializer accepts valid data. """
        data = {
            'company_name': 'ValidStartup',
            'team_size': 10,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2023,
            'email': 'valid@example.com',
        }
        serializer = serializers.ModelSerializer(instance=Startup, data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_invalid_data(self):
        """ Serializer rejects empty company_name. """
        data = {
            'company_name': '',
            'team_size': 10,
            'user': self.user.pk,
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2023,
            'email': 'valid@example.com',
        }
        serializer = serializers.ModelSerializer(instance=Startup, data=data)
        self.assertFalse(serializer.is_valid())






