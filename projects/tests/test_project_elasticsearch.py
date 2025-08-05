import pytest
from rest_framework.test import APIClient
from startups.models import Startup, Industry
from projects.models import Project
from projects.documents import ProjectDocument
from elasticsearch_dsl.connections import connections

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture(autouse=True)
def setup_data(db):
    connections.get_connection().indices.delete(index='*', ignore=[400, 404])
    ProjectDocument.init()

    it_industry = Industry.objects.create(name='IT')
    fintech_industry = Industry.objects.create(name='FinTech')
    startup = Startup.objects.create(
        company_name="Test Startup",
        description="Startup for testing projects",
        location="Lviv",
        funding_stage="series_a"
    )
    startup.industries.add(it_industry, fintech_industry)
    project = Project.objects.create(
        title="Smart Farm",
        description="An innovative farming project.",
        status="seed",
        required_amount=100000,
        startup=startup
    )
    
    ProjectDocument().update(project)
    connections.get_connection().indices.refresh(index=ProjectDocument._index.name)
    
    return project

@pytest.mark.django_db
def test_search_project_by_title(client, setup_data):
    response = client.get("/api/projects/search/", {"q": "Smart Farm"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["title"] == "Smart Farm"

@pytest.mark.django_db
def test_search_project_by_startup_name(client, setup_data):
    response = client.get("/api/projects/search/", {"q": "Test Startup"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["title"] == "Smart Farm"

@pytest.mark.django_db
def test_search_project_with_no_results(client, setup_data):
    response = client.get("/api/projects/search/", {"q": "non-existent_keyword"})
    assert response.status_code == 200
    assert len(response.data["results"]) == 0

@pytest.mark.django_db
def test_update_project_updates_index(client, setup_data):
    project = setup_data
    project.title = "Updated Smart Farm"
    project.save()
    ProjectDocument().update(project)
    connections.get_connection().indices.refresh(index=ProjectDocument._index.name)
    
    response = client.get("/api/projects/search/", {"q": "Updated Smart Farm"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["title"] == "Updated Smart Farm"

@pytest.mark.django_db
def test_delete_project_deletes_from_index(client, setup_data):
    project = setup_data
    project_id = project.id
    project.delete()
    ProjectDocument().delete(project_id)
    connections.get_connection().indices.refresh(index=ProjectDocument._index.name)
    
    response = client.get("/api/projects/search/", {"q": "Smart Farm"})
    assert response.status_code == 200
    assert len(response.data["results"]) == 0

@pytest.mark.django_db
def test_filter_project_by_status(client, setup_data):
    response = client.get("/api/projects/search/", {"status": "seed"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["title"] == "Smart Farm"

@pytest.mark.django_db
def test_healthcheck_view(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@pytest.mark.django_db
def test_empty_query(client, setup_data):
    response = client.get("/api/projects/search/", {})
    assert response.status_code == 200
    assert len(response.data["results"]) > 0

@pytest.mark.django_db
def test_multiple_filters_combined(client, setup_data):
    response = client.get("/api/projects/search/", {"q": "Farm", "status": "seed"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["title"] == "Smart Farm"