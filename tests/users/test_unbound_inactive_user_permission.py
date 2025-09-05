from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from tests.factories import StartupFactory, InvestorFactory
from users.permissions import HasActiveCompanyAccount

User = get_user_model()


class HasActiveCompanyAccountTests(TestCase):
    """Unit tests for the HasActiveCompanyAccount permission class."""

    def setUp(self):
        """Set up the RequestFactory and permission instance for tests."""
        self.factory = RequestFactory()
        self.permission = HasActiveCompanyAccount()

    def test_inactive_user_denied(self):
        """
        Test that a user with is_active=False is denied permission,
        regardless of company affiliation.
        """
        user = User.objects.create(is_active=False)
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_user_without_company_denied(self):
        """
        Test that an active user not linked to Startup or Investor
        is denied permission.
        """
        user = User.objects.create(is_active=True)
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_user_with_startup_allowed(self):
        """
        Test that an active user linked to a Startup is granted permission.
        """
        startup = StartupFactory()
        request = self.factory.get("/")
        request.user = startup.user
        self.assertTrue(self.permission.has_permission(request, None))

    def test_user_with_investor_allowed(self):
        """
        Test that an active user linked to an Investor is granted permission.
        """
        investor = InvestorFactory()
        request = self.factory.get("/")
        request.user = investor.user
        self.assertTrue(self.permission.has_permission(request, None))
