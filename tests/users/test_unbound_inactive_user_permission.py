import os
from django.test import TestCase, RequestFactory
from tests.factories import StartupFactory, InvestorFactory
from users.models import UserRole, User
from users.permissions import HasActiveCompanyAccount
from dotenv import load_dotenv

load_dotenv()
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")
TEST_EMAIL = "test@example.com"
TEST_FIRST_NAME = "Test"
TEST_LAST_NAME = "User"


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
        role_user, _ = UserRole.objects.get_or_create(role=UserRole.Role.STARTUP)
        user = User.objects.create_user(
            email=TEST_EMAIL,
            password=TEST_USER_PASSWORD,
            first_name=TEST_FIRST_NAME,
            last_name=TEST_LAST_NAME,
            role=role_user,
            is_active=False
        )
        request = self.factory.get("/")
        request.user = user
        self.assertFalse(self.permission.has_permission(request, None))

    def test_user_without_company_denied(self):
        """
        Test that an active user not linked to Startup or Investor
        is denied permission.
        """
        role_user, _ = UserRole.objects.get_or_create(role=UserRole.Role.STARTUP)
        user = User.objects.create_user(
            email="active_nocomp@example.com",
            password=TEST_USER_PASSWORD,
            first_name="Active",
            last_name="NoCompany",
            role=role_user,
            is_active=True
        )
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
