from django.test import TestCase
from startups.models import Industry
from tests.startups.test_disable_signal_mixin import DisableElasticsearchSignalsMixin
from tests.test_base_case import BaseAPITestCase

class IndustryModelTests(DisableElasticsearchSignalsMixin, BaseAPITestCase, TestCase):
    """ Tests for Industry model """

    def test_create_industry(self):
        """ Test that an Industry can be created successfully """
        industry, created = Industry.objects.get_or_create(name="Tech")
        self.assertEqual(industry.name, "Tech")
        self.assertIsNotNone(industry.pk)

