import pytest
from rest_framework.test import APIClient
from startups.models import Startup, Industry
from startups.documents import StartupDocument
from elasticsearch_dsl.connections import connections

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture(autouse=True)
def setup_data(db):
    connections.get_connection().indices.delete(index='*', ignore=[400, 404])
    StartupDocument.init()
    
    it_industry = Industry.objects.create(name='IT')
    ai_industry = Industry.objects.create(name='AI')
    startup = Startup.objects.create(
        company_name="Tech Innovators",
        description="A leading technology startup.",
        location="Kyiv",
        funding_stage="seed"
    )
    startup.industries.add(it_industry, ai_industry)
    
    StartupDocument().update(startup)
    connections.get_connection().indices.refresh(index=StartupDocument._index.name)
    
    return startup

@pytest.mark.django_db
def test_search_startup_by_name(client, setup_data):
    response = client.get("/api/startups/search/", {"q": "Tech Innovators"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["company_name"] == "Tech Innovators"

@pytest.mark.django_db
def test_search_startup_by_description(client, setup_data):
    response = client.get("/api/startups/search/", {"q": "leading technology"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["company_name"] == "Tech Innovators"

@pytest.mark.django_db
def test_update_startup_updates_index(client, setup_data):
    startup = setup_data
    startup.company_name = "Updated Innovators"
    startup.save()
    StartupDocument().update(startup)
    connections.get_connection().indices.refresh(index=StartupDocument._index.name)
    
    response = client.get("/api/startups/search/", {"q": "Updated Innovators"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["company_name"] == "Updated Innovators"

@pytest.mark.django_db
def test_delete_startup_deletes_from_index(client, setup_data):
    startup = setup_data
    startup_id = startup.id
    startup.delete()
    StartupDocument().delete(startup_id)
    connections.get_connection().indices.refresh(index=StartupDocument._index.name)
    
    response = client.get("/api/startups/search/", {"q": "Tech Innovators"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 0

@pytest.mark.django_db
def test_filter_startup_by_city(client, setup_data):
    response = client.get("/api/startups/search/", {"location": "Kyiv"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["company_name"] == "Tech Innovators"

@pytest.mark.django_db
def test_filter_startup_by_non_existent_city(client, setup_data):
    response = client.get("/api/startups/search/", {"location": "Lviv"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 0

@pytest.mark.django_db
def test_empty_query(client, setup_data):
    response = client.get("/api/startups/search/", {})
    assert response.status_code == 200
    assert len(response.data["results"]) > 0

@pytest.mark.django_db
def test_multiple_filters_combined(client, setup_data):
    response = client.get("/api/startups/search/", {"q": "Tech", "location": "Kyiv", "funding_stage": "seed"})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["company_name"] == "Tech Innovators"