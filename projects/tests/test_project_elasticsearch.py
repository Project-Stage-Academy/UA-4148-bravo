import pytest
from rest_framework.test import APIClient
from projects.models import Project
from projects.documents import ProjectDocument
from startups.models import Startup

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def sample_project(db):
    startup = Startup.objects.create(
        company_name="Test Startup",
        location="Lviv",
        funding_stage="seed",
        description="testing startup"
    )

    project = Project.objects.create(
        title="Smart Farm",
        description="IoT sensors for agriculture",
        status="seed",
        required_amount=100000,
        startup=startup
    )
    ProjectDocument().update(project)
    return project

@pytest.mark.django_db
def test_search_project_by_title(client, sample_project):
    response = client.get("/api/projects/search/", {"q": "Smart"})
    assert response.status_code == 200
    assert any("Smart" in item["title"] for item in response.data)

@pytest.mark.django_db
def test_filter_project_by_status(client, sample_project):
    response = client.get("/api/projects/search/", {"status": "seed"})
    assert response.status_code == 200
    assert all(item["status"] == "seed" for item in response.data)
