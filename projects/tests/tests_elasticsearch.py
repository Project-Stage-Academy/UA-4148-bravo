import pytest
from rest_framework.test import APIClient
from projects.models import Project
from startups.models import Startup

@pytest.fixture
def sample_startup(db):
    return Startup.objects.create(
        company_name="TestStartup",
        description="A startup description",
        funding_stage="Seed",
        location="Kyiv",
        industries="AI"
    )

@pytest.fixture
def sample_project(db, sample_startup):
    return Project.objects.create(
        title="Smart Project",
        description="An AI-based smart project",
        status="active",
        required_amount=50000,
        startup=sample_startup
    )

@pytest.mark.django_db
def test_search_projects(sample_project):
    client = APIClient()
    response = client.get('/api/projects/search/', {'q': 'smart'})
    assert response.status_code == 200
    assert any("Smart Project" in str(result) for result in response.data['results'])

@pytest.mark.django_db
def test_filter_projects(sample_project):
    client = APIClient()
    response = client.get('/api/projects/search/', {'status': 'active'})
    assert response.status_code == 200
    assert response.data['count'] >= 1
