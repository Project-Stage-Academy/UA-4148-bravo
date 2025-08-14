from django.core.exceptions import ValidationError
from startups.models import Industry
from tests.test_base_case import BaseAPITestCase


class IndustryModelCleanTests(BaseAPITestCase):
    """
    Tests for Industry.clean(): valid data passes, forbidden names raise errors.
    """

    def test_valid_industry_should_pass(self):
        """
        Industry with a valid name should pass clean() without ValidationError.
        """
        industry = Industry(name='Technology')
        try:
            industry.clean()
        except ValidationError:
            self.fail("clean() raised ValidationError unexpectedly.")

    def test_forbidden_name_should_raise(self):
        """
        Industry with a forbidden name should raise ValidationError containing 'name'.
        """
        industry = Industry(name='Other')
        with self.assertRaises(ValidationError) as context:
            industry.clean()
        self.assertIn('name', context.exception.message_dict)

