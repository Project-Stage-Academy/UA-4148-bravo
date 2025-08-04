import pytest
from rest_framework.test import APIClient
from startups.models import Startup
from startups.documents import StartupDocument
from elasticsearch_dsl.connections import connections
from django_elasticsearch_dsl.registries import registry

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def sample_startup(db):
    startup = Startup.objects.create(
        company_name="DeepAI Solutions",
        location="Kyiv",
        funding_stage="seed",
        description="Building AI tools for healthcare"
    )
    StartupDocument().update(startup)
    return startup

@pytest.fixture(autouse=True)
def clear_startup_index():
    connections.get_connection().indices.delete(index='startups', ignore=[400, 404])
    registry.update(StartupDocument)

@pytest.mark.django_db
def test_search_startup_by_name(client, sample_startup):
    response = client.get("/api/startups/search/", {"q": "DeepAI"})

    assert response.status_code == 200
    deepai_matches = [item["company_name"] for item in response.data if item["company_name"] == "DeepAI Solutions"]
    assert deepai_matches, f"Expected at least one match for 'DeepAI Solutions'. Got: {[item['company_name'] for item in response.data]}"

@pytest.mark.django_db
def test_filter_startup_by_location(client, sample_startup):
    response = client.get("/api/startups/search/", {"location": "Kyiv"})
    assert response.status_code == 200
    assert all(item["location"] == "Kyiv" for item in response.data)
