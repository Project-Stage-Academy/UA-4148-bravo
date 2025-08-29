from unittest import mock
from django.urls import reverse
from rest_framework.test import APITestCase
from startups.models import Startup, Location, Industry
from projects.models import Project, Category
from users.models import User, UserRole


class SearchTests(APITestCase):
    def setUp(self):
        """
        Setup test data for search tests:
        - Create role and user
        - Create location and industry
        - Create startup
        - Create project and category
        """

        # Ensure USER role exists
        role, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)

        # Create test user
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass1234",
            first_name="Test",
            last_name="User",
            role=role
        )

        # Create a location (required for Startup)
        self.location = Location.objects.create(
            country="US",
            region="California",
            city="San Francisco"
        )

        # Create an industry for the startup (required for Startup)
        self.industry = Industry.objects.create(
            name="AI",
            description="Artificial Intelligence"
        )

        # Create a startup associated with user, industry, and location
        self.startup = Startup.objects.create(
            user=self.user,
            company_name="Test Startup",
            description="AI powered solution",
            stage="seed",
            website="https://startup.com",
            founded_year=2023,
            industry=self.industry,
            location=self.location
        )

        # Create a category for the project
        self.category, _ = Category.objects.get_or_create(
            name="AI",
            defaults={"description": "AI related projects"}
        )

        # Create a project under the startup
        self.project = Project.objects.create(
            startup=self.startup,
            title="AI Platform",
            description="Project about machine learning",
            status="active",
            funding_goal=100000,
            current_funding=5000,
            category=self.category,
            email="project@example.com",
            website="https://project.com",
            is_active=True,
            is_participant=True
        )

    @mock.patch("search.views.StartupDocument.search")
    def test_startup_search_mocked(self, mock_search):
        """Test mocked search for startups."""
        mock_search.return_value = [mock.Mock(id=self.startup.id)]

        url = reverse("startup-search")
        response = self.client.get(url, {"q": "AI"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["company_name"], "Test Startup")

    @mock.patch("search.views.ProjectDocument.search")
    def test_project_search_mocked(self, mock_search):
        """Test mocked search for projects."""
        mock_search.return_value = [mock.Mock(id=self.project.id)]

        url = reverse("project-search")
        response = self.client.get(url, {"q": "AI"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "AI Platform")






