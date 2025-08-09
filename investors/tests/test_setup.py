from django.db.models.signals import post_save
from django.test import TestCase
from investors.models import Investor
from startups.models import Industry, Location
from startups.signals import update_startup_document
from users.models import UserRole, User
from rest_framework.test import APIClient


class BaseInvestorTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        post_save.disconnect(update_startup_document, sender=Investor)

    @classmethod
    def tearDownClass(cls):
        post_save.connect(update_startup_document, sender=Investor)
        super().tearDownClass()

    def setUp(self):
        role = UserRole.objects.get(role='user')
        self.user = User.objects.create_user(
            email='apiinvestor@example.com',
            password='pass12345',
            first_name='Api',
            last_name='Investor',
            role=role,
        )
        self.user.refresh_from_db()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.industry = Industry.objects.create(name="Technology")
        self.location = Location.objects.create(country="US")
