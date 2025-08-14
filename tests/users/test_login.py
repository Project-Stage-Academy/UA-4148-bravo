# Standard library
import uuid

# Django
from django.contrib.auth import get_user_model
from django.urls import reverse

# DRF
from rest_framework.test import APIClient

# Project-specific
from users.models import UserRole

# Pytest
from pytest import fixture, mark

User = get_user_model()


@fixture
def api_client():
    """Returns a DRF APIClient instance for making test requests."""
    return APIClient()


@fixture
def test_user(db):
    """
    Creates a test user with a randomized email and 'user' role.
    This avoids email collisions across tests.
    """
    role, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)
    unique_email = f"testuser_{uuid.uuid4().hex}@example.com"
    return User.objects.create_user(
        email=unique_email,
        password="testpass",
        first_name="Test",
        last_name="User",
        role=role,
        is_active=True
    )


@mark.django_db
def test_successful_login(api_client, test_user):
    """
    Should return access and refresh tokens for valid credentials.
    Also checks response structure, token format, and content type.
    """
    url = reverse("users:login")  # Or use hardcoded path if reverse not configured
    response = api_client.post(url, {
        "email": test_user.email,
        "password": "testpass"
    })

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"

    data = response.json()
    assert "access" in data and isinstance(data["access"], str) and data["access"]
    assert "refresh" in data and isinstance(data["refresh"], str) and data["refresh"]
    assert "user_id" in data and data["user_id"] == test_user.id
    assert "email" in data and data["email"] == test_user.email


@mark.django_db
def test_login_wrong_password(api_client, test_user):
    """
    Should return 401 Unauthorized for incorrect password.
    """
    url = reverse("users:login")
    response = api_client.post(url, {
        "email": test_user.email,
        "password": "wrongpass"
    })
    assert response.status_code == 401


@mark.django_db
def test_login_nonexistent_user(api_client):
    """
    Should return 401 Unauthorized for non-existent user.
    """
    url = reverse("users:login")
    response = api_client.post(url, {
        "email": "ghost@example.com",
        "password": "nopass"
    })
    assert response.status_code == 401


@mark.django_db
def test_login_missing_fields(api_client):
    """
    Should return 400 Bad Request when required fields are missing.
    """
    url = reverse("users:login")
    response = api_client.post(url, {
        "email": "testuser@example.com"
        # Missing password
    })
    assert response.status_code == 400

