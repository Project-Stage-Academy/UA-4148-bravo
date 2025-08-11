import datetime
from investors.serializers import InvestorSerializer
from tests.test_generic_case import DisableSignalMixinInvestor, BaseAPITestCase
from ddt import ddt, data, unpack


class InvestorSerializerValidDataTests(DisableSignalMixinInvestor, BaseAPITestCase):
    """Tests for valid investor data and some edge cases."""

    def test_valid_investor_data(self):
        """Test that the serializer accepts valid investor data."""
        data = {
            'company_name': 'API Investor',
            'email': 'investor@api.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 5,
            'stage': 'mvp',
            'fund_size': '1000000.00',
        }
        serializer = InvestorSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_very_long_company_name(self):
        """Test that the serializer accepts a very long but valid company name."""
        long_name = 'A' * 254
        data = {
            'company_name': long_name,
            'email': 'validemail@example.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 5,
            'stage': 'mvp',
            'fund_size': '100000.00',
        }
        serializer = InvestorSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_minimum_team_size(self):
        """Test that the serializer accepts the minimum valid team size of one."""
        data = {
            'company_name': 'Valid Company',
            'email': 'validemail@example.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 1,
            'stage': 'mvp',
            'fund_size': '100000.00',
        }
        serializer = InvestorSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_maximum_fund_size(self):
        """Test that the serializer accepts a very large fund size."""
        large_fund = '99999999999999999999.99'
        data = {
            'company_name': 'Valid Company',
            'email': 'validemail@example.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 5,
            'stage': 'mvp',
            'fund_size': large_fund,
        }
        serializer = InvestorSerializer(data=data)
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


@ddt
class InvestorSerializerInvalidFieldsTests(DisableSignalMixinInvestor, BaseAPITestCase):
    """Parameterized tests for invalid field values in the serializer."""

    @data(
        ('company_name', '   ', "Company name must not be empty."),
        ('email', 'invalid-email', None),
        ('fund_size', '-1000.00', None),
        ('founded_year', datetime.datetime.now().year + 1, None),
        ('team_size', 0, None),
        ('company_name', 'A' * 255, None),
    )
    @unpack
    def test_invalid_field_values(self, field, value, expected_error_msg):
        """
        Test that invalid values for fields cause serializer validation errors.

        Args:
            field (str): Field name to test.
            value: Invalid value to assign.
            expected_error_msg (str or None): Expected error message substring, if any.
        """
        data = {
            'company_name': 'Valid Company',
            'email': 'valid@example.com',
            'industry': self.industry.pk,
            'location': self.location.pk,
            'founded_year': 2020,
            'team_size': 5,
            'stage': 'mvp',
            'fund_size': '100000.00',
        }
        data[field] = value
        serializer = InvestorSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn(field, serializer.errors)
        if expected_error_msg:
            self.assertIn(expected_error_msg, serializer.errors[field][0])
