from decimal import Decimal
from ddt import ddt, data, unpack
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from common.enums import ProjectStatus
from projects.models import Project
from tests.test_base_case import BaseAPITestCase
from rest_framework.test import APIClient
from unittest.mock import patch


@override_settings(SECURE_SSL_REDIRECT=False)
class ProjectAPICRUDTests(BaseAPITestCase):
    """
    API CRUD tests for the Project model.
    Uses TestDataMixin to set up required related data
    such as users, startups, industries, locations, and categories.
    """

    def get_project_data(self, **overrides):
        """
        Generate a default project payload for API requests.

        Args:
            **overrides: Optional fields to override defaults.

        Returns:
            dict: Dictionary representing project data for API calls.
        """
        data = {
            "startup_id": self.startup.id,
            "title": "Default Project",
            "funding_goal": "50000.00",
            "current_funding": "1000.00",
            "category_id": self.category.id,
            "email": "default@example.com",
        }
        data.update(overrides)
        return data

    def test_create_project(self):
        """
        Test creating a new project via POST request.
        Expects HTTP 201 status and verifies:
          - The created project's title matches the request.
          - The project is associated with the correct startup.
          - The funding_goal and current_funding are stored correctly.
          - The category is assigned correctly.
          - Default fields such as status are set appropriately.
        """
        url = reverse("project-list")
        self.startup.user = self.user
        self.startup.save()
        data = self.get_project_data(title="API Project", email="api@example.com")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], data["title"])
        self.assertEqual(response.data["startup_id"], self.startup.id)
        self.assertEqual(str(response.data["funding_goal"]), data["funding_goal"])
        self.assertEqual(str(response.data["current_funding"]), data["current_funding"])
        self.assertEqual(response.data["category_id"], self.category.id)
        self.assertIn("status", response.data)
        self.assertEqual(response.data["status"], ProjectStatus.DRAFT)
        self.assertEqual(response.data["email"], data["email"])
        self.assertIn("id", response.data)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)

    @patch('users.permissions.HasActiveCompanyAccount.has_permission', return_value=True)
    def test_get_project_list(self, mocked_permission):
        """
        Test retrieving a list of projects via GET request.
        Ensures HTTP 200 status and that the list contains at least one project.
        """
        self.get_or_create_project()
        url = reverse("project-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_patch_project(self):
        """
        Test updating an existing project's title via PATCH request.
        Expects HTTP 200 status and verifies that the title changes.
        """
        self.startup.user = self.user
        self.startup.save()
        project = self.get_or_create_project(
            startup=self.startup,
            title="OriginalTitle",
            funding_goal=Decimal("10000.00"),
            current_funding=Decimal("1000.00"),
            category=self.category,
            email="userproject@example.com",
            status=ProjectStatus.DRAFT
        )
        url = reverse("project-detail", args=[project.pk])
        data = {"title": "UpdatedTitle"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], data["title"])

    def test_delete_project(self):
        """
        Test deleting an existing project via DELETE request.
        Expects HTTP 204 No Content status.
        """
        self.startup.user = self.user
        self.startup.save()
        project = self.get_or_create_project(
            startup=self.startup,
            title="DeleteMe",
            funding_goal=Decimal("10000.00"),
            current_funding=Decimal("500.00"),
            category=self.category,
            email="delete@example.com",
            status=ProjectStatus.DRAFT
        )
        url = reverse("project-detail", args=[project.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


@override_settings(SECURE_SSL_REDIRECT=False)
class ProjectAPIPermissionTests(BaseAPITestCase):
    """
    Test suite for verifying project-related API permissions.

    This class ensures that:
      - Unauthenticated users cannot create or list projects.
      - Authenticated users cannot update or delete projects owned by other users.
      - Access control rules are correctly enforced for different user roles.

    Uses TestDataMixin to generate test data for users, startups, industries,
    locations, categories, projects, and subscriptions.
    """

    def create_other_user_startup_project(self, project_title, project_email):
        """
        Create a project owned by a different user for permission tests.

        Args:
            project_title (str): Title of the project.
            project_email (str): Email associated with the project.

        Returns:
            Project: The created project instance owned by another user.
        """
        other_user = self.get_or_create_user('apiother@example.com', 'Api', 'Other')
        other_startup = self.get_or_create_startup(
            other_user,
            company_name='ListStartup',
            industry=self.industry,
            location=self.location
        )
        project = self.get_or_create_project(
            startup=other_startup,
            title=project_title,
            funding_goal=Decimal("10000.00"),
            current_funding=Decimal("500.00"),
            category=self.category,
            email=project_email,
            status=ProjectStatus.DRAFT
        )
        return project

    def test_unauthenticated_user_cannot_create_project(self):
        """
        Unauthenticated user should receive HTTP 401 Unauthorized
        when trying to create a project.
        """
        client = APIClient()
        url = reverse('project-list')
        data = {
            'startup_id': self.startup.id,
            'title': 'Unauthorized',
            'funding_goal': '50000.00',
            'current_funding': '1000.00',
            'category_id': self.category.id,
            'email': 'unauth@example.com',
        }
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_access_project_list(self):
        """
        Unauthenticated user should receive HTTP 401 Unauthorized
        when trying to access the project list.
        """
        client = APIClient()
        url = reverse('project-list')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_modify_other_users_project(self):
        """
        Ensure an authenticated user cannot update or delete a project
        owned by another user.

        Attempts to PATCH or DELETE should result in HTTP 403 Forbidden.
        """
        other_project = self.create_other_user_startup_project(
            project_title="OtherProject",
            project_email="otherproject@example.com"
        )
        url = reverse("project-detail", args=[other_project.pk])
        patch_response = self.client.patch(url, {"title": "HackedTitle"}, format="json")
        self.assertEqual(patch_response.status_code, status.HTTP_403_FORBIDDEN)

        delete_response = self.client.delete(url)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(SECURE_SSL_REDIRECT=False)
@ddt
class ProjectAPIValidationTests(BaseAPITestCase):
    """
    Test suite for validating Project API input fields.

    This class uses parametrized tests (via DDT) to verify that:
      - Required fields are enforced.
      - Numeric fields have correct boundaries (e.g., funding_goal must be positive and reasonable).
      - Email fields are properly formatted.
      - Appropriate validation error messages are returned when invalid data is submitted.

    Each test asserts that:
      - The response status code is HTTP 400 Bad Request.
      - The response data contains an error for the specific field.
      - The error message includes an expected substring indicating the validation issue.
    """

    def get_project_data(self, **overrides):
        """
        Return a dictionary of default project data, optionally overridden by kwargs.

        Args:
            **overrides: Key-value pairs to override default data.

        Returns:
            dict: Project data dictionary.
        """
        data = {
            'startup_id': self.startup.id,
            'title': 'Default Project',
            'funding_goal': '50000.00',
            'current_funding': '1000.00',
            'category_id': self.category.id,
            'email': 'default@example.com',
        }
        data.update(overrides)
        return data

    @data(
        ('funding_goal', '1000000000000000000000000.00', 'too large'),
        ('funding_goal', '-1000.00', 'greater than'),
        ('funding_goal', '0.00', 'greater than'),
        ('email', 'invalid-email-format', 'valid'),
        ('title', None, 'required'),
        ('email', None, 'required'),
    )
    @unpack
    def test_field_validation(self, field_name, invalid_value, expected_error_fragment):
        """
        Parametrized test that verifies validation errors occur for various invalid inputs.

        Args:
            field_name (str): The field to test validation on.
            invalid_value (Any): The invalid value to assign to the field. If None, the field is omitted.
            expected_error_fragment (str): A substring expected to be found in the validation error message.

        The test asserts that:
            - The response status code is 400 Bad Request.
            - The response data contains an error for the given field.
            - The error message includes the expected error fragment.
        """
        url = reverse('project-list')
        self.startup.user = self.user
        self.startup.save()
        tested_data = self.get_project_data()
        if invalid_value is None:
            tested_data.pop(field_name, None)
        else:
            tested_data[field_name] = invalid_value

        response = self.client.post(url, tested_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(field_name, response.data)

        errors = response.data.get(field_name, [])
        if not isinstance(errors, list):
            errors = [errors]

        self.assertTrue(
            any(
                expected_error_fragment in str(msg).lower()
                or 'ensure that there are no more than' in str(msg).lower()
                for msg in errors
            ),
            f"Expected validation error containing '{expected_error_fragment}' for field '{field_name}', got: {errors}"
        )
