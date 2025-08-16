# tests/startups/test_startup_model.py
from django.core.exceptions import ValidationError
from django.test import TestCase
from common.enums import Stage
from startups.models import Startup
from tests.startups.test_disable_signal_mixin import DisableElasticsearchSignalsMixin
from tests.test_base_case import BaseAPITestCase


class StartupModelCleanTests(DisableElasticsearchSignalsMixin, BaseAPITestCase, TestCase):
    """Tests for Startup.clean() and model validations."""

    def test_valid_clean_should_pass(self):
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
            self.fail(f"ValidationError raised unexpectedly: {e}")

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
        self.assertIn('unknown', errors)

    def test_missing_required_fields_should_raise(self):
        startup = Startup(user=self.user, founded_year=2022, industry=self.industry, location=self.location)
        with self.assertRaises(ValidationError):
            startup.full_clean()

    def test_default_stage_is_set_if_missing(self):
        startup = Startup(user=self.user, company_name='DefaultStageStartup', founded_year=2020, industry=self.industry, location=self.location)
        self.assertEqual(startup.stage, Stage.IDEA)
        startup.save()
        startup.refresh_from_db()
        self.assertEqual(startup.stage, Stage.IDEA)
