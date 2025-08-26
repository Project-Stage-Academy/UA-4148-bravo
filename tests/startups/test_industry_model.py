from tests.test_base_case import BaseAPITestCase
from startups.models import Industry
from django.core.exceptions import ValidationError


class IndustryModelCleanTests(BaseAPITestCase):
    """
    Test suite for validating the `clean()` method of the Industry model.
    Ensures that valid data passes validation and forbidden names raise errors.
    """

    def test_valid_industry_should_pass(self):
        """
        Test that an Industry instance with a valid name
        passes the `clean()` method without raising ValidationError.
        """
        industry = Industry(name='Technology')
        try:
            industry.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly.")

    def test_forbidden_name_should_raise(self):
        """
        Test that an Industry instance with a forbidden name
        raises ValidationError containing 'name' in the message_dict.
        """
        industry = Industry(name='Other')
        with self.assertRaises(ValidationError) as context:
            industry.clean()
        self.assertIn('name', context.exception.message_dict)
