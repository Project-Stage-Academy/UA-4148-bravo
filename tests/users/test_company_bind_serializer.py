from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from users.serializers.company_bind_serializer import CompanyBindingSerializer

User = get_user_model()


class CompanyBindingSerializerTests(APITestCase):
    """Tests for CompanyBindingSerializer validation logic"""

    def setUp(self):
        self.valid_data = {
            'company_name': 'Valid Company Name',
            'company_type': 'startup'
        }

    def test_serializer_valid_data(self):
        """Test that serializer validates correct data"""
        serializer = CompanyBindingSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_missing_required_fields(self):
        """Test that serializer requires both fields"""
        test_cases = [
            ({'company_type': 'startup'}, 'company_name'),
            ({'company_name': 'Test Company'}, 'company_type'),
            ({}, 'company_name'),
        ]

        for data, expected_error_field in test_cases:
            with self.subTest(data=data):
                serializer = CompanyBindingSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn(expected_error_field, serializer.errors)

    def test_serializer_invalid_company_type(self):
        """Test that serializer rejects invalid company type"""
        data = {**self.valid_data, 'company_type': 'invalid_type'}
        serializer = CompanyBindingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('company_type', serializer.errors)

    def test_serializer_valid_company_types(self):
        """Test that serializer accepts both valid company types"""
        for company_type in ['startup', 'investor']:
            with self.subTest(company_type=company_type):
                data = {**self.valid_data, 'company_type': company_type}
                serializer = CompanyBindingSerializer(data=data)
                self.assertTrue(serializer.is_valid())

    def test_serializer_company_name_validation(self):
        """Test company name validation scenarios"""
        test_cases = [
            ('', False, 'cannot be empty'),
            ('   ', False, 'cannot be empty'),
            ('Valid Name', True, None),
            ('Valid-Name', True, None),
            ("Valid's Name", True, None),
            ('Company 123', True, None),
            ('Компанія', False, 'Latin letters'),
            ('Company@Test', False, 'Latin letters'),
            ('A' * 254, True, None),  # Max length
            ('A' * 255, False, '254 characters'),  # Too long
        ]

        for name, should_be_valid, error_contains in test_cases:
            with self.subTest(name=name):
                data = {**self.valid_data, 'company_name': name}
                serializer = CompanyBindingSerializer(data=data)

                if should_be_valid:
                    self.assertTrue(serializer.is_valid(),
                                    f"Expected valid for '{name}' but got errors: {serializer.errors}")
                else:
                    self.assertFalse(serializer.is_valid())
                    self.assertIn('company_name', serializer.errors)
                    if error_contains:
                        self.assertIn(error_contains, str(serializer.errors['company_name']))

    def test_serializer_forbidden_company_names(self):
        """Test that serializer rejects forbidden company names"""
        forbidden_names = ['other', 'Other', 'OTHER', 'none', 'NONE', 'misc', 'MISC', 'default', 'DEFAULT']

        for name in forbidden_names:
            with self.subTest(name=name):
                data = {**self.valid_data, 'company_name': name}
                serializer = CompanyBindingSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn('company_name', serializer.errors)
                self.assertIn('generic or reserved', str(serializer.errors['company_name']))

    def test_serializer_whitespace_trimming(self):
        """Test that serializer trims whitespace from company names"""
        data = {**self.valid_data, 'company_name': '  Test Company  '}
        serializer = CompanyBindingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['company_name'], 'Test Company')

    def test_serializer_data_type_conversion(self):
        """Test that serializer handles different data types correctly"""
        test_cases = [
            (123, '123', True),
            (None, None, False),
        ]

        for input_value, expected_value, should_be_valid in test_cases:
            with self.subTest(input_value=input_value):
                data = {**self.valid_data, 'company_name': input_value}
                serializer = CompanyBindingSerializer(data=data)

                if should_be_valid:
                    self.assertTrue(serializer.is_valid())
                    self.assertEqual(serializer.validated_data['company_name'], expected_value)
                else:
                    self.assertFalse(serializer.is_valid())

    def test_serializer_extra_fields_ignored(self):
        """Test that extra fields are ignored during validation"""
        data = {
            'company_name': 'Test Company',
            'company_type': 'startup',
            'extra_field': 'should be ignored',
            'another_extra': 123
        }
        serializer = CompanyBindingSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('extra_field', serializer.validated_data)
        self.assertNotIn('another_extra', serializer.validated_data)
