import threading
import time
from decimal import Decimal, ROUND_DOWN
from django.db import transaction
from django.test import TransactionTestCase
from rest_framework import serializers
from rest_framework.test import APIClient
from common.enums import Stage
from investments.serializers.subscription_create import SubscriptionCreateSerializer
from investments.services.subscriptions import get_total_subscribed
from tests.elasticsearch.factories import UserFactory, IndustryFactory, LocationFactory, StartupFactory, ProjectFactory, \
    CategoryFactory


class SubscriptionSerializerConcurrencyTests(TransactionTestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = UserFactory.create()
        cls.user2 = UserFactory.create()

        cls.industry1 = IndustryFactory.create(name="Fintech")
        cls.industry2 = IndustryFactory.create(name="E-commerce")
        cls.location1 = LocationFactory.create(country="US")
        cls.location2 = LocationFactory.create(country="DE")

        cls.startup1 = StartupFactory.create(
            user=cls.user1,
            industry=cls.industry1,
            location=cls.location1,
            company_name="Fintech Solutions",
            stage=Stage.IDEA,
        )
        cls.startup2 = StartupFactory.create(
            user=cls.user2,
            industry=cls.industry2,
            location=cls.location2,
            company_name="ShopFast",
            stage=Stage.MVP,
        )

        cls.category1 = CategoryFactory.create(name="Tech")
        cls.category2 = CategoryFactory.create(name="Finance")

        cls.project1 = ProjectFactory.create(
            startup=cls.startup1,
            category=cls.category1,
            title="First Test Project",
            funding_goal=Decimal("1000.00")
        )
        cls.project2 = ProjectFactory.create(
            startup=cls.startup2,
            category=cls.category2,
            title="Second Test Project",
            funding_goal=Decimal("2000.00")
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.__class__.user1)

    def get_subscription_data(self, investor, project, amount):
        return {
            "investor": investor.id,
            "project": project.id,
            "amount": amount
        }

    def test_concurrent_subscriptions(self):
        amount1 = (self.project1.funding_goal * Decimal("0.6")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        amount2 = (self.project1.funding_goal * Decimal("0.5")).quantize(Decimal("0.01"), rounding=ROUND_DOWN)

        errors = []

        def subscribe(investor, amount, delay=0):
            time.sleep(delay)
            data = self.get_subscription_data(investor, self.project1, amount)
            serializer = SubscriptionCreateSerializer(data=data)
            try:
                with transaction.atomic():
                    if serializer.is_valid(raise_exception=True):
                        serializer.save()
            except serializers.ValidationError as e:
                errors.append(e.detail)

        t1 = threading.Thread(target=subscribe, args=(self.user1, amount1, 0))
        t2 = threading.Thread(target=subscribe, args=(self.user2, amount2, 0.1))  # другий потік із невеликою затримкою

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        total = get_total_subscribed(project=self.project1)

        self.assertLessEqual(total, self.project1.funding_goal)

        error_messages = [
            str(e).lower()
            for err in errors
            for e in (err.get('amount') or [])
        ]
        self.assertTrue(
            any("exceeds funding goal" in msg for msg in error_messages),
            f"Expected funding goal exceeded error, got: {error_messages}"
        )
