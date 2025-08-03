import pytest
from rest_framework.test import APIClient
from startups.models import Startup

@pytest.mark.django_db
def test_startup_search(api_client):
    Startup.objects.create(title="Green Energy", description="Solar panels", status="open", required_amount=1000)
    response = api_client.get('/api/projects/search/', {'q': 'Solar'})
    assert response.status_code == 200
