from users.models import User, UserRole
import os
from dotenv import load_dotenv

load_dotenv()

TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")


class UserMixin:
    """
    Mixin providing utility methods for creating and managing User instances used in tests.
    """

    @classmethod
    def create_user(cls, email, first_name, last_name):
        """
        Create and return a new User instance with a default password and role USER.

        Args:
            email (str): Email address for the user.
            first_name (str): User's first name.
            last_name (str): User's last name.

        Returns:
            User: Newly created User instance.
        """
        role_user, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)
        return User.objects.create_user(
            email=email,
            password=TEST_USER_PASSWORD,
            first_name=first_name,
            last_name=last_name,
            role=role_user
        )

    @classmethod
    def setup_users(cls):
        """
        Create several default User instances for testing and assign them as class attributes.

        Creates three users:
        - cls.user
        - cls.user2
        - cls.user_startup

        Raises:
            AssertionError: If the expected number of users are not created.
        """
        cls.user = cls.create_user("user1@example.com", "Investor", "One")
        cls.user2 = cls.create_user("user2@example.com", "Investor", "Two")
        cls.user_startup = cls.create_user("userstartup@example.com", "Startup", "User")

        assert User.objects.count() >= 3, "Users not created properly"

    @classmethod
    def setup_all(cls):
        """
        Convenience method to setup all necessary users.
        """
        cls.setup_users()

    @classmethod
    def tear_down(cls):
        """
        Clean up User instances created during tests to avoid polluting other test cases.

        Deletes users tracked in the class attribute '_created_users', if it exists.
        """
        if hasattr(cls, '_created_users'):
            for user in cls._created_users:
                User.objects.filter(pk=user.pk).delete()
