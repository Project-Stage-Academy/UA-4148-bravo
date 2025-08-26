import threading
import time
from decimal import Decimal

from django.db import transaction, connections
from django.test import TransactionTestCase
from rest_framework import serializers
from django.db import close_old_connections
from common.enums import Stage
from investments.serializers.subscription_create import SubscriptionCreateSerializer
from investments.services.subscriptions import get_total_subscribed
from investors.models import Investor
from tests.factories import UserFactory, IndustryFactory, LocationFactory, StartupFactory, ProjectFactory, \
    CategoryFactory


class SubscriptionSerializerConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        close_old_connections()
        for conn in connections.all():
            conn.close()

    def setUp(self):
        self.user1 = UserFactory.create()
        self.user2 = UserFactory.create()

        self.industry1 = IndustryFactory.create(name="Fintech")
        self.industry2 = IndustryFactory.create(name="E-commerce")
        self.location1 = LocationFactory.create(country="US")
        self.location2 = LocationFactory.create(country="DE")

        self.startup1 = StartupFactory.create(
            user=self.user1,
            industry=self.industry1,
            location=self.location1,
            company_name="Fintech Solutions",
            stage=Stage.IDEA,
        )
        self.investor1 = Investor.objects.create(
            user=self.user1,
            industry=self.industry1,
            company_name="Investor One",
            location=self.location1,
            email="investor1great@example.com",
            founded_year=2000,
            stage=Stage.MVP,
            fund_size=Decimal("1000000.00")
        )

        self.investor2 = Investor.objects.create(
            user=self.user2,
            industry=self.industry2,
            company_name="Investor Two",
            location=self.location2,
            email="investor2great@example.com",
            founded_year=2005,
            stage=Stage.MVP,
            fund_size=Decimal("2000000.00")
        )

        self.user3 = UserFactory.create()
        self.investor3 = Investor.objects.create(
            user=self.user3,
            industry=self.industry1,
            company_name="Investor Three",
            location=self.location1,
            email="investor3@example.com",
            founded_year=2010
        )

        self.category1 = CategoryFactory.create(name="Tech")

        self.project1 = ProjectFactory.create(
            startup=self.startup1,
            category=self.category1,
            title="First Test Project",
            funding_goal=Decimal("1000.00")
        )

    def get_subscription_data(self, investor, project, amount):
        """
        Return subscription data for the serializer.
        Only 'amount' is passed in data; project and investor are provided via context.
        """
        return {
            "amount": amount
        }

    def test_concurrent_subscriptions(self):
        """
        Test that concurrent subscription attempts do not exceed the project's funding goal.
        One of the subscriptions should fail with a "funding goal exceeded" error.
        """
        amount1 = Decimal("600.00")
        amount2 = Decimal("500.00")

        errors = []

        def subscribe(investor, amount, delay=0):
            close_old_connections()
            time.sleep(delay)
            data = self.get_subscription_data(investor, self.project1, amount)
            class DummyRequest:
                def __init__(self, user):
                    self.user = user
    
            serializer = SubscriptionCreateSerializer(
                data=data,
                context={'request': DummyRequest(investor.user), 'project': self.project1}
            )
    
            try:
                serializer.is_valid(raise_exception=True)
                with transaction.atomic():
                    serializer.save() 
            except serializers.ValidationError as e:
                errors.append(e.detail)

        t1 = threading.Thread(target=subscribe, args=(self.investor2, amount1, 0))
        t2 = threading.Thread(target=subscribe, args=(self.investor3, amount2, 0.05))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        for conn in connections.all():
            conn.close()

        total = get_total_subscribed(project=self.project1)
        self.assertLessEqual(total, self.project1.funding_goal)

        error_messages = [
            str(e).lower()
            for err in errors
            for e in (err.values() if isinstance(err, dict) else [err])
        ]
        self.assertTrue(
            any("exceeds funding goal" in msg for msg in error_messages),
            f"Expected funding goal exceeded error, got: {error_messages}"
        )
