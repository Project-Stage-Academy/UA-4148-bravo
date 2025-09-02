import os
import mongomock
from django.test import TestCase
from mongoengine import connect, disconnect
from users.models import User, UserRole

TEST_EMAIL_1 = "user1@example.com"
TEST_EMAIL_2 = "user2@example.com"
TEST_EMAIL_3 = "user3@example.com"
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "default_test_password")


class BaseChatTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        role_startup, _ = UserRole.objects.get_or_create(role=UserRole.Role.STARTUP)
        role_investor, _ = UserRole.objects.get_or_create(role=UserRole.Role.INVESTOR)

        cls.user1 = User.objects.create_user(
            email=TEST_EMAIL_1,
            password=TEST_USER_PASSWORD,
            first_name="First",
            last_name="User",
            role=role_startup,
        )
        cls.user2 = User.objects.create_user(
            email=TEST_EMAIL_2,
            password=TEST_USER_PASSWORD,
            first_name="Second",
            last_name="User",
            role=role_investor,
        )
        cls.user3 = User.objects.create_user(
            email=TEST_EMAIL_3,
            password=TEST_USER_PASSWORD,
            first_name="Third",
            last_name="User",
            role=role_investor,
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        disconnect()
        connect(
            db="mongoenginetest",
            host="mongodb://localhost",
            mongo_client_class=mongomock.MongoClient,
            alias="chat_test"
        )

    @classmethod
    def tearDownClass(cls):
        disconnect(alias="chat_test")
        super().tearDownClass()
