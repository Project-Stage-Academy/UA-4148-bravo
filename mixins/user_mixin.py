from users.models import User, UserRole
import os
from dotenv import load_dotenv

load_dotenv()

TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")


class UserMixin:
    @classmethod
    def create_user(cls, email, first_name, last_name):
        """
        Create and return a new User instance with default password and role USER.

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
        cls.user = cls.create_user("user1@example.com", "Investor", "One")
        cls.user2 = cls.create_user("user2@example.com", "Investor", "Two")
        cls.user_startup = cls.create_user("userstartup@example.com", "Startup", "User")

        assert User.objects.count() >= 3, "Users not created properly"

    @classmethod
    def setup_all(cls):
        cls.setup_users()
