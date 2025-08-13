import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError

from investors.models import Investor
from tests.test_base_case import BaseAPITestCase


class InvestorModelCleanTests(BaseAPITestCase):
    """
    Unit tests for the Investor model's validation logic.

    This test suite verifies that the Investor model's full_clean and clean methods
    enforce field requirements and constraints correctly, including:
    - Required fields presence
    - Valid ranges for numeric and date fields
    - Business rules like minimum description length
    - Proper default values assignment
    """

    def test_valid_clean_should_pass(self):
        """
        Test that an Investor instance with all valid fields passes full validation.
        """
        investor = Investor(
            user=self.user,
            company_name='InvestX',
            founded_year=2020,
            industry=self.industry,
            location=self.location,
            fund_size=Decimal('1000000.00'),
            stage=Investor.stage.field.default,
            email='investx@example.com'
        )
        try:
            investor.full_clean()
        except ValidationError:
            self.fail("Investor.full_clean() raised ValidationError unexpectedly")

    def test_missing_required_fields_should_fail(self):
        """
        Test that missing required fields raise ValidationError.
        """
        investor = Investor()
        with self.assertRaises(ValidationError) as cm:
            investor.full_clean()
        errors = cm.exception.message_dict
        self.assertIn('user', errors)
        self.assertIn('company_name', errors)
        self.assertIn('founded_year', errors)
        self.assertIn('industry', errors)
        self.assertIn('location', errors)
        self.assertIn('email', errors)

    def test_invalid_founded_year_should_fail(self):
        """
        Test that founded_year outside valid range (less than 1900 or future year)
        raises ValidationError.
        """
        investor = Investor(
            user=self.user,
            company_name='InvestInvalidYear',
            founded_year=1800,
            industry=self.industry,
            location=self.location,
            fund_size=Decimal('10000.00'),
            email='testinvalidinvestor@example.com',
            stage=Investor.stage.field.default
        )
        with self.assertRaises(ValidationError) as cm:
            investor.full_clean()
        self.assertIn('founded_year', cm.exception.message_dict)

        future_year = datetime.datetime.now().year + 1
        investor.founded_year = future_year
        with self.assertRaises(ValidationError) as cm:
            investor.full_clean()
        self.assertIn('founded_year', cm.exception.message_dict)

    def test_negative_fund_size_should_fail(self):
        """
        Test that negative fund_size raises ValidationError.
        """
        investor = Investor(
            user=self.user,
            company_name='InvestNegativeFund',
            founded_year=2020,
            industry=self.industry,
            location=self.location,
            fund_size=Decimal('-100.00'),
            email='testnegfund@example.com',
            stage='mvp'
        )
        with self.assertRaises(ValidationError) as cm:
            investor.full_clean()
        self.assertIn('fund_size', cm.exception.message_dict)

    def test_short_description_should_fail(self):
        """
        Test that a description shorter than 10 chars raises ValidationError.
        This tests the abstract Company.clean() method indirectly.
        """
        investor = Investor(
            user=self.user,
            company_name='InvestDescFail',
            founded_year=2020,
            industry=self.industry,
            location=self.location,
            fund_size=Decimal('1000.00'),
            email='descfail@example.com',
            stage='mvp',
            description='Too short'
        )
        with self.assertRaises(ValidationError) as cm:
            investor.full_clean()
        self.assertIn('description', cm.exception.message_dict)

    def test_default_stage_is_set_if_missing(self):
        """
        Test that stage is set to default Stage.MVP if not provided.
        """
        investor = Investor(
            user=self.user,
            company_name='InvestDefaultStage',
            founded_year=2020,
            industry=self.industry,
            location=self.location,
            fund_size=Decimal('50000.00'),
            email='defaultstage@example.com'
        )
        investor.full_clean()
        investor.clean()
        self.assertEqual(investor.stage, Investor.stage.field.default)
