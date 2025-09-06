from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
from datetime import timedelta
from common.enums import Stage
from startups.models import Startup, Industry, Location
from tests.factories import UserFactory
from users.tasks import check_unbound_inactive_users
from django.core.cache import cache


class CheckUnboundInactiveUsersTests(TestCase):
    """Unit tests for the check_unbound_inactive_users Celery task."""

    @patch("users.tasks.send_mail")
    def test_unbound_users_receive_email(self, mock_send_mail):
        """
        Test that active users without a linked Startup or Investor
        receive a reminder email.
        """
        cache.clear()

        user = UserFactory(is_active=True)

        check_unbound_inactive_users()

        self.assertTrue(mock_send_mail.called)

        called_emails = [args[3][0] for args, kwargs in mock_send_mail.call_args_list]
        self.assertIn(user.email, called_emails)

    @patch("users.tasks.send_mail")
    def test_inactive_recent_users_receive_email(self, mock_send_mail):
        """
        Test that active users who haven't performed actions in the
        last 7 days receive a reminder email.
        """
        cache.clear()

        user = UserFactory(
            is_active=True,
            last_action_at=timezone.now() - timedelta(days=10)
        )

        check_unbound_inactive_users()

        self.assertTrue(mock_send_mail.called)

        called_emails = [args[3][0] for args, kwargs in mock_send_mail.call_args_list]
        self.assertIn(user.email, called_emails)

    @patch("users.tasks.send_mail")
    def test_active_recent_users_do_not_receive_email(self, mock_send_mail):
        """
        Test that active users who are bound to a Startup or Investor
        do not receive a reminder email.
        """
        user = UserFactory(is_active=True)

        Startup.objects.create(
            user=user,
            industry=Industry.objects.first() or Industry.objects.create(name="Tech"),
            company_name="Bound Startup",
            location=Location.objects.first() or Location.objects.create(country="US", city="NYC", region="NY"),
            email="bound@example.com",
            founded_year=2023,
            team_size=5,
            stage=Stage.SEED,
        )

        check_unbound_inactive_users()

        self.assertFalse(mock_send_mail.called)
