import pytest
from rest_framework.test import APIClient
from projects.models import Project

@pytest.mark.django_db
def test_project_search(api_client):
    Project.objects.create(title="Green Energy", description="Solar panels", status="open", required_amount=1000)
    response = api_client.get('/api/projects/search/', {'q': 'Solar'})
    assert response.status_code == 200

