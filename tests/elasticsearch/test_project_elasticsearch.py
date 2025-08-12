import time

from django.conf import settings
from django.urls import reverse
from elasticsearch_dsl import Index
from elasticsearch_dsl.connections import connections
from rest_framework import status

from projects.documents import ProjectDocument
from tests.test_base import BaseAPITestCase, DisableSignalMixinStartup


class ProjectElasticsearchTests(DisableSignalMixinStartup, BaseAPITestCase):
    """
    Test suite for Project Elasticsearch integration and API behavior,
    using factory-based setup from ProjectTestSetupMixin.
    Includes tests for search, filters, validation, permissions, and edge cases.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up Elasticsearch connection before any tests run,
        reading hosts from Django settings or defaulting to localhost.
        """
        super().setUpClass()
        es_config = getattr(settings, 'ELASTICSEARCH_DSL', {}).get('default', {})
        hosts = es_config.get('hosts', 'http://localhost:9200')
        connections.configure(default={'hosts': hosts})

    def setUp(self):
        """
        Create and configure Elasticsearch index before each test.
        Authenticate the client as user1.
        Adds a short delay to allow Elasticsearch to index data.
        """
        self.index = Index('projects')
        try:
            self.index.delete()
        except:
            pass

        self.index.create()
        ProjectDocument._doc_type.mapping.save('projects')

        self.client.force_authenticate(user=self.user1)

        time.sleep(1)

    def tearDown(self):
        """
        Delete Elasticsearch index after each test to clean up.
        """
        try:
            self.index.delete()
        except:
            pass

    def test_empty_query_returns_all_projects(self):
        """
        Test that querying the project list with no filters
        returns all existing projects with HTTP 200 OK.
        """
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_no_results_for_non_existent_title(self):
        """
        Test that searching for a non-existent project title
        returns an empty list with HTTP 200 OK.
        """
        url = reverse('project-list')
        response = self.client.get(url, {'search': 'nonexistent_project'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_combined_filters_work_correctly(self):
        """
        Test filtering projects by category name and startup company name
        returns the correct project with HTTP 200 OK.
        """
        url = reverse('projectdocument-list')
        response = self.client.get(url, {
            'category.name': 'Tech',
            'startup.company_name': 'Fintech Solutions'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "First Test Project")

    def test_invalid_filter_field_returns_bad_request(self):
        """
        Test that using an invalid filter field returns HTTP 400 Bad Request.
        """
        url = reverse('projectdocument-list')
        response = self.client.get(url, {'nonexistent_field': 'value'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_project_missing_required_fields(self):
        """
        Test that creating a project without required fields
        'title' and 'email' results in HTTP 400 Bad Request
        with appropriate error messages.
        """
        url = reverse('project-list')
        data = {
            'startup_id': self.startup1.id,
            'funding_goal': '10000.00',
            'current_funding': '0.00',
            'category_id': self.category1.id,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
        self.assertIn('email', response.data)

    def test_create_project_invalid_funding_goal(self):
        """
        Test that creating a project with a negative funding goal
        returns HTTP 400 Bad Request with error for 'funding_goal'.
        """
        url = reverse('project-list')
        data = {
            'startup_id': self.startup1.id,
            'title': 'Invalid Funding',
            'funding_goal': '-500',
            'current_funding': '0.00',
            'category_id': self.category1.id,
            'email': 'invalidfunding@example.com',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('funding_goal', response.data)

    def test_permission_denied_for_other_user_update(self):
        """
        Test that the authenticated user cannot update a project
        belonging to another user, receiving HTTP 403 Forbidden.
        """
        project = self.project2  # belongs to user2
        url = reverse('project-detail', args=[project.pk])
        data = {'title': 'Unauthorized Update'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permission_denied_for_unauthenticated_user_access(self):
        """
        Test that unauthenticated users cannot access the project list,
        receiving HTTP 401 Unauthorized.
        """
        self.client.force_authenticate(user=None)
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_funding_goal_edge_case_large_value(self):
        """
        Test creating a project with an extremely large funding goal value.
        Accepts either success (201 Created) or validation failure (400 Bad Request)
        depending on validation rules.
        """
        url = reverse('project-list')
        data = {
            'startup_id': self.startup1.id,
            'title': 'Large Funding Goal',
            'funding_goal': '9999999999999999999999.99',
            'current_funding': '0.00',
            'category_id': self.category1.id,
            'email': 'largefund@example.com',
        }
        response = self.client.post(url, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

    def test_create_project_with_invalid_funding_goal_type(self):
        """
        Attempt to create a project with a funding_goal value that cannot be converted to Decimal.
        Expects HTTP 400 Bad Request with validation error on funding_goal.
        """
        url = reverse('project-list')
        data = {
            'startup_id': self.startup1.id,
            'title': 'Invalid Funding Type',
            'funding_goal': 'invalid_decimal',
            'current_funding': '0.00',
            'category_id': self.category1.id,
            'email': 'invalidtype@example.com',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('funding_goal', response.data)

    def test_current_funding_cannot_exceed_funding_goal(self):
        """
        Attempt to create a project where current_funding exceeds funding_goal.
        Expects HTTP 400 Bad Request with validation error on current_funding.
        """
        url = reverse('project-list')
        data = {
            'startup_id': self.startup1.id,
            'title': 'Funding Exceeded',
            'funding_goal': '1000.00',
            'current_funding': '2000.00',
            'category_id': self.category1.id,
            'email': 'fundingexceeded@example.com',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('current_funding', response.data)

    def test_update_project_startup_id_forbidden(self):
        """
        Attempt to update the startup_id of an existing project.
        Expects either an error response (HTTP 400 or 403) or that the field remains unchanged on HTTP 200.
        """
        project = self.project1
        url = reverse('project-detail', args=[project.pk])
        new_startup_id = self.startup2.id
        data = {'startup_id': new_startup_id}
        response = self.client.patch(url, data, format='json')

        self.assertIn(response.status_code,
                      [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN, status.HTTP_200_OK])

        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(response.data['startup_id'], project.startup_id)

    def test_delete_nonexistent_project_returns_404(self):
        """
        Attempt to delete a project with a non-existent ID.
        Expects HTTP 404 Not Found response.
        """
        url = reverse('project-detail', args=[999999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_partial_title_match_returns_results(self):
        """
        Search for projects by partial match in the title.
        Expects at least one project in the response matching the search term.
        """
        url = reverse('project-list')
        search_term = 'First Test'
        response = self.client.get(url, {'search': search_term})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertTrue(any(search_term.lower() in proj['title'].lower() for proj in response.data))
