import pytest
from rest_framework.test import APIClient
from startups.models import Startup

@pytest.fixture
def sample_startup(db):
    return Startup.objects.create(
        company_name="GreenTech",
        description="Startup for green energy",
        funding_stage="Series A",
        location="Lviv",
        industries="GreenTech"
    )

@pytest.mark.django_db
def test_search_startup_by_name(sample_startup):
    client = APIClient()
    response = client.get('/api/startups/search/', {'q': 'green'})
    assert response.status_code == 200
    assert any("GreenTech" in str(result) for result in response.data['results'])

@pytest.mark.django_db
def test_filter_startup_by_location(sample_startup):
    client = APIClient()
    response = client.get('/api/startups/search/', {'location': 'Lviv'})
    assert response.status_code == 200
    assert response.data['count'] >= 1
