from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from tests.test_setup import BaseProjectTestCase
from ddt import ddt, data, unpack


class ProjectAPICRUDTests(BaseProjectTestCase):
    def get_project_data(self, **overrides):
        """
        Generate default project data dictionary, with optional overrides.

        Args:
            **overrides: Fields to override default values.

        Returns:
            dict: Project data for API requests.
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

    def test_create_project(self):
        """
        Test creating a new project via POST request returns HTTP 201 and
        the created project's title matches the input.
        """
        url = reverse('project-list')
        data = self.get_project_data(title='API Project', email='api@example.com')
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], data['title'])

    def test_get_project_list(self):
        """
        Test retrieving a list of projects returns HTTP 200 and at least
        one project is present in the response.
        """
        self.create_project(
            startup=self.startup,
            title='ListProject',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('500.00'),
            category=self.category,
            email='list@example.com'
        )
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_update_project(self):
        """
        Test partial update (PATCH) of a project's title returns HTTP 200
        and the updated title matches the input.
        """
        project = self.create_project(
            startup=self.startup,
            title='UpdateMe',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('500.00'),
            category=self.category,
            email='update@example.com'
        )
        url = reverse('project-detail', args=[project.pk])
        data = {'title': 'UpdatedTitle'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], data['title'])

    def test_delete_project(self):
        """
        Test deleting an existing project via DELETE request returns HTTP 204 No Content.
        """
        project = self.create_project(
            startup=self.startup,
            title='DeleteMe',
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('500.00'),
            category=self.category,
            email='delete@example.com'
        )
        url = reverse('project-detail', args=[project.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ProjectAPIPermissionTests(BaseProjectTestCase):
    def create_other_user_startup_project(self, project_title, project_email):
        """
        Create a project owned by a different user for permission tests.

        Args:
            project_title (str): Title of the other user's project.
            project_email (str): Email associated with the other user's project.

        Returns:
            Project: The created Project instance owned by another user.
        """
        other_user = self.create_user(
            email='apiother@example.com',
            first_name='Api',
            last_name='Other'
        )
        other_startup = self.create_startup(
            user=other_user,
            company_name='ListStartup',
            founded_year=2019,
            industry=self.industry,
            location=self.location
        )
        project = self.create_project(
            startup=other_startup,
            title=project_title,
            funding_goal=Decimal('10000.00'),
            current_funding=Decimal('500.00'),
            category=self.category,
            email=project_email
        )
        return project

    def test_unauthenticated_user_cannot_create_project(self):
        """
        Verify that an unauthenticated user attempting to create a project
        receives an HTTP 401 Unauthorized response.
        """
        self.client.logout()
        url = reverse('project-list')
        data = {
            'startup_id': self.startup.id,
            'title': 'Unauthorized',
            'funding_goal': '50000.00',
            'current_funding': '1000.00',
            'category_id': self.category.id,
            'email': 'unauth@example.com',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_access_project_list(self):
        """
        Verify that an unauthenticated user cannot access the project list endpoint,
        receiving an HTTP 401 Unauthorized response.
        """
        self.client.logout()
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_update_other_users_project(self):
        """
        Ensure that a user cannot update a project owned by another user,
        receiving an HTTP 403 Forbidden response.
        """
        project = self.create_other_user_startup_project('OtherProject', 'other@example.com')
        url = reverse('project-detail', args=[project.pk])
        data = {'title': 'HackedTitle'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_cannot_delete_other_users_project(self):
        """
        Ensure that a user cannot delete a project owned by another user,
        receiving an HTTP 403 Forbidden response.
        """
        project = self.create_other_user_startup_project('OtherDelete', 'otherdelete@example.com')
        url = reverse('project-detail', args=[project.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@ddt
class ProjectAPIValidationTests(BaseProjectTestCase):
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
        data = self.get_project_data()

        if invalid_value is None:
            data.pop(field_name, None)
        else:
            data[field_name] = invalid_value

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(field_name, response.data)
        self.assertTrue(
            any(expected_error_fragment in str(msg).lower() for msg in response.data[field_name]),
            f"Expected validation error containing '{expected_error_fragment}' for field '{field_name}', got: {response.data[field_name]}"
        )
