import os
import uuid
import logging
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from rest_framework.test import APITestCase
from unittest.mock import patch
from users.models import User, UserRole
from utils.authenticate_client import authenticate_client

logger = logging.getLogger(__name__)
DEBUG_LOGS = os.environ.get("DEBUG_TEST_LOGS") == "1"

NON_EXISTENT_USER_ID = 999_999
ALLOWED_THROTTLE_REQUESTS = getattr(settings, "API_THROTTLE_LIMIT", 5)


@override_settings(SECURE_SSL_REDIRECT=False)
class ResendEmailTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_role, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)

    def setUp(self):
        self.user = self._create_test_user()
        if DEBUG_LOGS:
            logger.info("Created test user: %s", self.user.email)

    def _create_test_user(self, email=None, is_active=False, token='oldtoken'):
        return User.objects.create(
            email=email or f"user_{uuid.uuid4().hex[:10]}@example.com",
            first_name='Test',
            last_name='User',
            role=self.user_role,
            is_active=is_active,
            email_verification_token=token,
            email_verification_sent_at=timezone.now()
        )

    def perform_resend_email_test(self, target_user_id, expected_status=202, email=None, user_obj=None):
        url = reverse('resend-email')
        data = {'user_id': target_user_id}
        if email:
            data['email'] = email

        response = self.client.post(url, data, format='json')

        if user_obj:
            user_obj.refresh_from_db()

        self.assertEqual(response.status_code, expected_status)

        if expected_status == 202 and DEBUG_LOGS:
            logger.info("Received 202 response with detail: %s", response.data.get('detail'))

        return response

    @patch('users.views.email_views.ResendEmailView.throttle_classes', new=[])
    @patch('users.views.email_views.send_mail')
    @patch('users.views.email_views.EMAIL_VERIFICATION_TOKEN.make_token', return_value='newtoken')
    def test_resend_email_scenarios(self, mock_make_token, mock_send_mail):
        scenarios = [
            ("happy_path", None, True),
            ("email_override", "newemail@example.com", True),
            ("unknown_user", None, False),
        ]

        for scenario, email, send_mail_expected in scenarios:
            with self.subTest(scenario=scenario, email=email):
                if scenario == "unknown_user":
                    target_user_id = NON_EXISTENT_USER_ID
                    test_user = None
                else:
                    test_user = self._create_test_user(email=email)
                    target_user_id = test_user.user_id

                response = self.perform_resend_email_test(target_user_id, user_obj=test_user, email=email)

                if scenario != "unknown_user":
                    self.assertIn('verification email', response.data.get('detail', ''))

                if test_user:
                    self.assertTrue(test_user.email.endswith('@example.com'))
                    if email:
                        self.assertEqual(test_user.pending_email, email)
                    else:
                        self.assertIsNone(test_user.pending_email)

                if send_mail_expected:
                    self.assertIsNotNone(mock_send_mail.call_args)
                    _, kwargs = mock_send_mail.call_args
                    recipient_list = kwargs.get('recipient_list', [])
                    self.assertIsNotNone(recipient_list)
                    if email:
                        self.assertIn(email, recipient_list)
                else:
                    mock_send_mail.assert_not_called()

                mock_send_mail.reset_mock()

    @patch('users.views.email_views.ResendEmailView.throttle_classes', [])
    def test_bad_input_invalid_emails(self):
        invalid_emails = [
            "plainaddress",
            "@missingusername.com",
            "user@.com",
            "user@domain..com",
            "user@domain,com",
            "user@domain com",
        ]

        url = reverse('resend-email')

        for email in invalid_emails:
            with self.subTest(email=email):
                data = {'user_id': self.user.user_id, 'email': email}
                response = self.client.post(url, data, format='json')
                self.user.refresh_from_db()

                self.assertEqual(response.status_code, 400)
                self.assertIn('email', response.data)
                expected_error = 'Enter a valid email address.'
                errors = response.data['email']
                if isinstance(errors, list):
                    self.assertTrue(any(expected_error in str(e) for e in errors))
                else:
                    self.assertIn(expected_error, str(errors))
                self.assertTrue(self.user.email.startswith('user_'))
                if DEBUG_LOGS:
                    logger.info("Invalid email '%s' correctly rejected", email)

    @patch('users.views.email_views.send_mail')
    @patch('users.views.email_views.EMAIL_VERIFICATION_TOKEN.make_token', return_value='newtoken')
    def test_throttling_with_limit(self, mock_make_token, mock_send_mail):
        url = reverse('resend-email')
        data = {'user_id': self.user.user_id}
        authenticate_client(self.client, self.user)

        for i in range(ALLOWED_THROTTLE_REQUESTS):
            with self.subTest(request_number=i + 1):
                response = self.client.post(url, data, format='json')
                self.assertEqual(response.status_code, 202)
                self.user.refresh_from_db()
                self.assertTrue(self.user.email.startswith('user_'))
                if DEBUG_LOGS:
                    logger.info("Throttling test: request %d successful", i + 1)

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(mock_send_mail.call_count, ALLOWED_THROTTLE_REQUESTS)
        if DEBUG_LOGS:
            logger.info("Throttling limit reached as expected after %d requests", ALLOWED_THROTTLE_REQUESTS)

    @patch('users.views.email_views.ResendEmailView.throttle_classes', [])
    @patch('users.views.email_views.send_mail')
    def test_already_verified_user(self, mock_send_mail):
        active_user = self._create_test_user(
            email=f"active_{uuid.uuid4().hex[:10]}@example.com",
            is_active=True,
            token=None
        )
        if DEBUG_LOGS:
            logger.info("Already verified user created: %s", active_user.email)

        self.perform_resend_email_test(active_user.user_id, user_obj=active_user)
        mock_send_mail.assert_called_once()
        if DEBUG_LOGS:
            logger.info("Already verified user test: email send attempted but user already active")
