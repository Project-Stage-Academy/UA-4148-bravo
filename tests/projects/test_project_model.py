from decimal import Decimal
from ddt import ddt, data, unpack
from django.core.exceptions import ValidationError
from projects.models import Project, ProjectStatus
from tests.test_base_case import BaseAPITestCase


@ddt
class ProjectModelCleanTests(BaseAPITestCase):
    """
    Test suite for the Project model's clean() method validation logic.
    Uses DDT for parameterized scenarios.
    """

    def create_project(self, **overrides):
        """Helper to create a Project instance with defaults and overrides."""
        defaults = {
            'startup': self.startup,
            'title': 'DefaultProject',
            'funding_goal': Decimal('10000.00'),
            'current_funding': Decimal('0.00'),
            'category': self.category,
            'email': f'{overrides.get("title", "default").lower()}@example.com',
            'status': ProjectStatus.DRAFT,
            'is_participant': False,
            'business_plan': None
        }
        defaults.update(overrides)
        return Project(**defaults)

    @data(
        ('current_funding', {'current_funding': Decimal('20000.00')}, 'current_funding'),
        ('business_plan', {'status': ProjectStatus.IN_PROGRESS, 'business_plan': None}, 'business_plan'),
        ('business_plan', {'status': ProjectStatus.COMPLETED, 'business_plan': None}, 'business_plan'),
        ('funding_goal', {'is_participant': True, 'funding_goal': None}, 'funding_goal'),
        ('multiple', {
            'current_funding': Decimal('20000.00'),
            'status': ProjectStatus.COMPLETED,
            'business_plan': None
        }, None),
    )
    @unpack
    def test_clean_should_raise_for_invalid_cases(self, case_name, overrides, expected_field):
        """
        Parametrized test to check all invalid cases in Project.clean().
        """
        project = self.create_project(title=case_name, **overrides)
        with self.assertRaises(ValidationError) as context:
            project.clean()

        errors = context.exception.message_dict
        if expected_field:
            self.assertIn(expected_field, errors)
        else:
            self.assertIn('current_funding', errors)
            self.assertIn('business_plan', errors)

    def test_clean_should_pass_for_valid_data(self):
        """
        Ensure clean() passes without errors for valid project data.
        """
        project = self.create_project(
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('5000.00'),
            status=ProjectStatus.IN_PROGRESS,
            business_plan='projects/business_plans/plan.pdf'
        )
        try:
            project.clean()
        except ValidationError as e:
            self.fail(f"clean() raised ValidationError unexpectedly: {e}")
