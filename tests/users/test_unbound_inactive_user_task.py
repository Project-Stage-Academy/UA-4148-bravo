from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
from datetime import timedelta
from tests.factories import UserFactory
from users.tasks import check_unbound_inactive_users


class CheckUnboundInactiveUsersTests(TestCase):
    """Unit tests for the check_unbound_inactive_users Celery task."""

    @patch("users.tasks.send_mail")
    def test_unbound_users_receive_email(self, mock_send_mail):
        """
        Test that active users without a linked Startup or Investor
        receive a reminder email.
        """
        user = UserFactory(is_active=True)
        check_unbound_inactive_users()
        self.assertTrue(mock_send_mail.called)
        _, kwargs = mock_send_mail.call_args
        self.assertIn(user.email, kwargs["recipient_list"])

    @patch("users.tasks.send_mail")
    def test_inactive_recent_users_receive_email(self, mock_send_mail):
        """
        Test that active users who haven't performed actions in the
        last 7 days receive a reminder email.
        """
        user = UserFactory(
            is_active=True,
            last_action_at=timezone.now() - timedelta(days=10)
        )
        check_unbound_inactive_users()
        self.assertTrue(mock_send_mail.called)
        _, kwargs = mock_send_mail.call_args
        self.assertIn(user.email, kwargs["recipient_list"])

    @patch("users.tasks.send_mail")
    def test_active_recent_users_do_not_receive_email(self, mock_send_mail):
        """
        Test that active users who have been recently active (within 7 days)
        do not receive a reminder email.
        """
        UserFactory(
            is_active=True,
            last_action_at=timezone.now()
        )
        check_unbound_inactive_users()
        self.assertFalse(mock_send_mail.called)
