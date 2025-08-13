import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from users.models import UserRole

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def test_user(db):
    role, _ = UserRole.objects.get_or_create(role="user")  # или нужная роль
    return User.objects.create_user(
        email="testuser@example.com",
        password="testpass",
        first_name="Test",
        last_name="User",
        role=role,
        is_active=True
    )

@pytest.mark.django_db
def test_successful_login(api_client, test_user):
    response = api_client.post("/api/v1/auth/jwt/create/", {
        "email": "testuser@example.com",
        "password": "testpass"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access" in data
    assert "refresh" in data
    assert data["user_id"] == test_user.id
    assert data["email"] == test_user.email

@pytest.mark.django_db
def test_login_wrong_password(api_client, test_user):
    response = api_client.post("/api/v1/auth/jwt/create/", {
        "email": "testuser@example.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401

@pytest.mark.django_db
def test_login_nonexistent_user(api_client):
    response = api_client.post("/api/v1/auth/jwt/create/", {
        "email": "ghost@example.com",
        "password": "nopass"
    })
    assert response.status_code == 401

@pytest.mark.django_db
def test_login_missing_fields(api_client):
    response = api_client.post("/api/v1/auth/jwt/create/", {
        "email": "testuser@example.com"
    })
    assert response.status_code == 400
