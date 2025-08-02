import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user(db):
    return User.objects.create_user(username="testuser", password="testpass")

@pytest.mark.django_db
def test_successful_login(api_client, test_user):
    response = api_client.post("/api/users/login/", {
        "username": "testuser",
        "password": "testpass"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access" in data
    assert "refresh" in data
    assert data["user_id"] == test_user.id
    assert data["username"] == test_user.username

@pytest.mark.django_db
def test_login_wrong_password(api_client, test_user):
    response = api_client.post("/api/users/login/", {
        "username": "testuser",
        "password": "wrongpass"
    })
    assert response.status_code == 401

@pytest.mark.django_db
def test_login_nonexistent_user(api_client):
    response = api_client.post("/api/users/login/", {
        "username": "ghost",
        "password": "nopass"
    })
    assert response.status_code == 401

@pytest.mark.django_db
def test_login_missing_fields(api_client):
    response = api_client.post("/api/users/login/", {
        "username": "testuser"
    })
    assert response.status_code == 400


