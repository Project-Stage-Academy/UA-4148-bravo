import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch
from django.utils import timezone
from users.models import User, UserRole

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_role():
    role, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)
    return role

@pytest.fixture
def user(user_role):
    return User.objects.create(
        email='user@example.com',
        first_name='Test',
        last_name='User',
        role=user_role,
        is_active=False,
        email_verification_token='oldtoken',
        email_verification_sent_at=timezone.now()
    )

@pytest.mark.django_db
@patch('django.core.mail.send_mail')
def test_happy_path(mock_send_mail, api_client, user):
    url = reverse('resend-email')
    data = {'user_id': user.user_id, 'token': ''}

    response = api_client.post(url, data, format='json')

    user.refresh_from_db()

    assert response.status_code == 202
    mock_send_mail.assert_called_once()
    assert user.pending_email is None

@pytest.mark.django_db
@patch('django.core.mail.send_mail')
def test_unknown_user_id_returns_202_no_exception(mock_send_mail, api_client):
    url = reverse('resend-email')
    data = {'user_id': 999999, 'token': ''}

    response = api_client.post(url, data, format='json')

    assert response.status_code == 202
    mock_send_mail.assert_not_called()

@pytest.mark.django_db
@patch('django.core.mail.send_mail')
def test_email_override_saves_pending_and_sends_to_override(mock_send_mail, api_client, user):
    url = reverse('resend-email')
    new_email = 'newemail@example.com'
    data = {'user_id': user.user_id, 'email': new_email, 'token': ''}

    response = api_client.post(url, data, format='json')

    user.refresh_from_db()
    assert response.status_code == 202
    assert user.pending_email == new_email
    mock_send_mail.assert_called_once()
    args, kwargs = mock_send_mail.call_args
    assert new_email in kwargs['recipient_list']

@pytest.mark.django_db
@patch('users.views.ResendEmailView.throttle_classes', [])
@patch('django.core.mail.send_mail')
def test_throttling(mock_send_mail, api_client, user):
    url = reverse('resend-email')
    data = {'user_id': user.user_id, 'token': ''}

    for _ in range(5):
        response = api_client.post(url, data, format='json')
        assert response.status_code == 202
    
    response = api_client.post(url, data, format='json')
    assert response.status_code == 202  

@pytest.mark.django_db
def test_bad_input_invalid_email(api_client, user):
    url = reverse('resend-email')
    data = {'user_id': user.user_id, 'email': 'not-an-email', 'token': ''}

    response = api_client.post(url, data, format='json')

    assert response.status_code == 400
    assert 'email' in response.data

@pytest.mark.django_db
@patch('django.core.mail.send_mail')
def test_already_verified_user_returns_202_no_email_sent(mock_send_mail, api_client, user_role):
    user = User.objects.create(
        email='active@example.com',
        first_name='Active',
        last_name='User',
        role=user_role,
        is_active=True
    )
    url = reverse('resend-email')
    data = {'user_id': user.user_id, 'token': ''}

    response = api_client.post(url, data, format='json')

    assert response.status_code == 202
    mock_send_mail.assert_not_called()

@pytest.mark.django_db
@patch('users.views.send_mail')
def test_email_override_saves_pending_and_sends_to_override(mock_send_mail, api_client, user):
    url = reverse('resend-email')
    new_email = 'newemail@example.com'
    data = {'user_id': user.user_id, 'email': new_email, 'token': ''}

    response = api_client.post(url, data, format='json')

    print("Response status:", response.status_code)
    print("Response data:", response.data)

    user.refresh_from_db()
    assert response.status_code == 202, f"Unexpected status: {response.status_code}, data: {response.data}"
    assert user.pending_email == new_email
    mock_send_mail.assert_called_once()
    args, kwargs = mock_send_mail.call_args
    assert new_email in kwargs['recipient_list']