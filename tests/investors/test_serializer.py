import datetime
from common.enums import Stage
from investors.serializers.investor import InvestorSerializer
from ddt import ddt, data, unpack
from tests.test_base_case import BaseAPITestCase


class InvestorSerializerValidDataTests(BaseAPITestCase):
    """Tests for valid investor data and some edge cases."""

    def test_valid_investor_data(self):
        """Test that the serializer accepts valid investor data."""
        validate_data = {
            'company_name': 'API Investor',
            'email': 'investor@api.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 5,
            'stage': Stage.MVP,
            'fund_size': '1000000.00',
        }
        serializer = InvestorSerializer(data=validate_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_very_long_company_name(self):
        """Test that the serializer accepts a very long but valid company name."""
        long_name = 'A' * 254
        invalid_company_name_data = {
            'company_name': long_name,
            'email': 'validemail@example.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 5,
            'stage': Stage.LAUNCH,
            'fund_size': '1000000.00',
        }
        serializer = InvestorSerializer(data=invalid_company_name_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_minimum_team_size(self):
        """Test that the serializer accepts the minimum valid team size of one."""
        minimum_team_size_data = {
            'company_name': 'Valid Company',
            'email': 'validemail@example.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 1,
            'stage': Stage.MVP,
            'fund_size': '100000.00',
        }
        serializer = InvestorSerializer(data=minimum_team_size_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_maximum_fund_size(self):
        """Test that the serializer accepts a very large fund size."""
        large_fund = '999999999999999999.99'
        maximum_fund_size_data = {
            'company_name': 'Valid Company',
            'email': 'validemail@example.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 5,
            'stage': Stage.MVP,
            'fund_size': large_fund,
        }
        serializer = InvestorSerializer(data=maximum_fund_size_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_missing_required_fields(self):
        """
        Test that missing required fields cause validation errors
        with clear and informative messages.
        """
        serializer = InvestorSerializer(data={})
        self.assertFalse(serializer.is_valid())

        required_fields = ['company_name', 'email', 'industry', 'location', 'founded_year']
        for field in required_fields:
            self.assertIn(field, serializer.errors)
            self.assertTrue(len(serializer.errors[field]) > 0, f"Error message missing for {field}")

    def test_short_description_should_fail(self):
        """Description < 10 chars should raise validation error."""
        data = {
            'company_name': 'ShortDesc',
            'email': 'shortdesc@example.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 5,
            'stage': Stage.MVP,
            'fund_size': '100000.00',
            'description': 'Too short'
        }
        serializer = InvestorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('description', serializer.errors)


@ddt
class InvestorSerializerInvalidFieldsTests(BaseAPITestCase):
    """Parameterized tests for invalid field values in the serializer."""

    @data(
        ('company_name', '   ', "Company name must not be empty."),
        ('company_name', 'A' * 255, "Company name cannot exceed 254 characters."),
        ('email', 'invalid-email', "Invalid email address format."),
        ('fund_size', '-1000.00', "Ensure this value is greater than or equal to 0."),
        ('fund_size', '99999999999999999999.99', "Fund size is too large."),
        ('founded_year', datetime.datetime.now().year + 1, "Ensure this value is less than or equal to"),
        ('team_size', 0, "Ensure this value is greater than or equal to 1."),
        ('stage', 'INVALID_STAGE', "Invalid stage choice."),
        ('description', 'Too short', "Description must be at least 10 characters long if provided.")
    )
    @unpack
    def test_invalid_field_values(self, field, value, expected_error_msg):
        """
        Test that invalid values for fields cause serializer validation errors.

        Args:
            field (str): Field name to test.
            value: Invalid value to assign.
            expected_error_msg (str): Expected error message substring.
        """
        valid_data = {'company_name': "Valid Company", 'email': "valid@example.com", 'industry': self.industry.pk,
                      'location': self.location.pk, 'founded_year': 2020, 'team_size': 5, 'stage': Stage.MVP,
                      'fund_size': "100000.00", 'description': "This is a valid description.", field: value}
        serializer = InvestorSerializer(data=valid_data)
        self.assertFalse(serializer.is_valid(), f"{field} with value {value} unexpectedly passed validation.")
        self.assertIn(field, serializer.errors)
        if expected_error_msg:
            error_text = str(serializer.errors[field][0])
            self.assertIn(expected_error_msg, error_text,
                          f"{field} error message '{error_text}' does not contain '{expected_error_msg}'")
