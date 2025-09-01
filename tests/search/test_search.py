# from unittest import mock
# from django.urls import reverse
# from rest_framework.test import APITestCase
# from startups.models import Startup, Industry, Location
# from projects.models import Project
# from users.models import User, UserRole
#
#
# class SearchTests(APITestCase):
#     def setUp(self):
#         # Create user role
#         role, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)
#
#         # Create user
#         self.user = User.objects.create_user(
#             email="test@example.com",
#             password="password123",
#             role=role,
#         )
#
#         # Create industry (required for Startup)
#         self.industry = Industry.objects.create(name="Healthcare")
#
#         # Create location (required for Startup) using ISO code
#         self.location = Location.objects.create(city="Kyiv", country="UA")
#
#         # Create startup with all required fields
#         self.startup = Startup.objects.create(
#             user=self.user,
#             company_name="Test Startup",
#             description="AI Startup in healthcare",
#             stage="seed",
#             founded_year=2020,
#             industry=self.industry,
#             location=self.location,
#         )
#
#         # Create project linked to startup
#         self.project = Project.objects.create(
#             startup=self.startup,
#             title="Health AI",
#             description="AI project for healthcare",
#             status="active",
#             funding_goal=10000,
#         )
#
#     @mock.patch("search.views.StartupDocument.search")
#     def test_startup_search_mocked(self, mock_search):
#         """Test startup search with mocked Elasticsearch"""
#
#         # Prepare mock search result
#         mock_execute = mock.Mock()
#         mock_execute.__iter__ = lambda s: iter([mock.Mock(id=self.startup.id)])
#         mock_search.return_value.execute.return_value = mock_execute
#
#         # Call API
#         url = reverse("startup-search")
#         response = self.client.get(url, {"q": "AI"})
#
#         # Assertions
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(len(response.data), 1)
#         self.assertEqual(response.data[0]["company_name"], "Test Startup")
#
#     @mock.patch("search.views.ProjectDocument.search")
#     def test_project_search_mocked(self, mock_search):
#         """Test project search with mocked Elasticsearch"""
#
#         # Prepare mock search result
#         mock_execute = mock.Mock()
#         mock_execute.__iter__ = lambda s: iter([mock.Mock(id=self.project.id)])
#         mock_search.return_value.execute.return_value = mock_execute
#
#         # Call API
#         url = reverse("project-search")
#         response = self.client.get(url, {"q": "AI"})
#
#         # Assertions
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(len(response.data), 1)
#         self.assertEqual(response.data[0]["title"], "Health AI")
#
#     def test_startup_search_empty_query(self):
#         """Test empty query for startups should return empty list"""
#         url = reverse("startup-search")
#         response = self.client.get(url, {"q": ""})
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(len(response.data), 0)
#
#     def test_project_search_empty_query(self):
#         """Test empty query for projects should return empty list"""
#         url = reverse("project-search")
#         response = self.client.get(url, {"q": ""})
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(len(response.data), 0)











