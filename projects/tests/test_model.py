from decimal import Decimal

from django.core.exceptions import ValidationError

from projects.models import Project
from tests.test_generic_case import DisableSignalMixinStartup, BaseAPITestCase


class ProjectModelCleanTests(DisableSignalMixinStartup, BaseAPITestCase):
    """
    Test suite for the Project model's clean() method validation logic,
    ensuring that business rules are enforced before saving.
    """

    def test_clean_should_raise_for_invalid_funding(self):
        """
        Validate that the clean() method raises ValidationError if
        current_funding exceeds funding_goal.
        """
        project = Project(
            startup=self.startup,
            title='BadFunding',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('20000.00'),
            category=self.category,
            email='bad@example.com'
        )
        with self.assertRaises(ValidationError) as context:
            project.clean()
        self.assertIn('current_funding', context.exception.message_dict)

    def test_clean_should_raise_for_missing_plan(self):
        """
        Validate that the clean() method raises ValidationError if
        a project marked as 'completed' status does not have a business_plan.
        """
        project = Project(
            startup=self.startup,
            title='MissingPlan',
            status='completed',
            funding_goal=Decimal('50000.00'),
            current_funding=Decimal('10000.00'),
            category=self.category,
            email='missing@example.com'
        )
        with self.assertRaises(ValidationError) as context:
            project.clean()
        self.assertIn('business_plan', context.exception.message_dict)
