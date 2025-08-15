import uuid
import logging
import os
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from unittest.mock import patch
from users.models import User, UserRole

logger = logging.getLogger(__name__)
DEBUG_LOGS = os.environ.get("DEBUG_TEST_LOGS") == "1"

class ResendEmailTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user_role, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)

    def setUp(self):
        self.user = User.objects.create(
            email=f"user_{uuid.uuid4().hex[:10]}@example.com",
            first_name='Test',
            last_name='User',
            role=self.user_role,
            is_active=False,
            email_verification_token='oldtoken',
            email_verification_sent_at=timezone.now()
        )
        if DEBUG_LOGS:
            logger.info("Created test user: %s", self.user.email)

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

    @patch('users.views.ResendEmailView.throttle_classes', [])
    @patch('users.views.send_mail')
    @patch('users.views.EMAIL_VERIFICATION_TOKEN.make_token', return_value='newtoken')
    def test_resend_email_scenarios(self, mock_make_token, mock_send_mail):
        scenarios = [
            ("happy_path", None, None, True),
            ("email_override", "newemail@example.com", "newemail@example.com", True),
            ("unknown_user", None, None, False),
        ]

        for i, (scenario, email, expected_pending_email, send_mail_expected) in enumerate(scenarios):
            if scenario == "unknown_user":
                target_user_id = 999999
                test_user = None
            else:
                test_user = User.objects.create(
                    email=f"user_{uuid.uuid4().hex[:10]}@example.com",
                    first_name='Test',
                    last_name='User',
                    role=self.user_role,
                    is_active=False,
                    email_verification_token='oldtoken',
                    email_verification_sent_at=timezone.now()
                )
                target_user_id = test_user.user_id

            response = self.perform_resend_email_test(target_user_id, user_obj=test_user, email=email)

            if scenario in ["happy_path", "email_override"]:
                self.assertIn('verification email', response.data['detail'])

            if test_user:
                if expected_pending_email:
                    self.assertEqual(test_user.pending_email, expected_pending_email)
                else:
                    self.assertIsNone(test_user.pending_email)
                self.assertTrue(test_user.email.endswith('@example.com'))

            if send_mail_expected:
                mock_send_mail.assert_called()
                if email:
                    _, kwargs = mock_send_mail.call_args
                    self.assertIn(email, kwargs['recipient_list'])
            else:
                mock_send_mail.assert_not_called()

            mock_send_mail.reset_mock()

    @patch('users.views.ResendEmailView.throttle_classes', [])
    def test_bad_input_invalid_email(self):
        url = reverse('resend-email')
        data = {'user_id': self.user.user_id, 'email': 'not-an-email'}

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
            logger.info("Bad input test: invalid email correctly rejected")

    @patch('users.views.send_mail')
    @patch('users.views.EMAIL_VERIFICATION_TOKEN.make_token', return_value='newtoken')
    def test_throttling_with_limit(self, mock_make_token, mock_send_mail):
        url = reverse('resend-email')
        data = {'user_id': self.user.user_id}
        allowed_requests = 5

        for i in range(allowed_requests):
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, 202)
            self.user.refresh_from_db()
            self.assertTrue(self.user.email.startswith('user_'))
            if DEBUG_LOGS:
                logger.info("Throttling test: request %d successful", i + 1)

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(mock_send_mail.call_count, allowed_requests)
        if DEBUG_LOGS:
            logger.info("Throttling limit reached as expected after %d requests", allowed_requests)

    @patch('users.views.ResendEmailView.throttle_classes', [])
    @patch('users.views.send_mail')
    def test_already_verified_user(self, mock_send_mail):
        active_user = User.objects.create(
            email=f"active_{uuid.uuid4().hex[:10]}@example.com",
            first_name='Active',
            last_name='User',
            role=self.user_role,
            is_active=True,
            email_verification_token=None,
            email_verification_sent_at=None
        )
        if DEBUG_LOGS:
            logger.info("Already verified user created: %s", active_user.email)

        self.perform_resend_email_test(active_user.user_id, user_obj=active_user)
        mock_send_mail.assert_called_once()
        if DEBUG_LOGS:
            logger.info("Already verified user test: email send attempted but user already active")
