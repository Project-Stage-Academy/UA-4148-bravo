import threading
import time
from decimal import Decimal
from django.db import transaction, connections, close_old_connections
from django.test import TransactionTestCase
from rest_framework import serializers

from common.enums import Stage
from investments.serializers.subscription_create import SubscriptionCreateSerializer
from investments.services.subscriptions import get_total_subscribed
from tests.setup_tests_data import TestDataMixin
from tests.test_disable_signal_mixin import DisableSignalsMixin
from projects.models import Project


class SubscriptionSerializerConcurrencyTests(DisableSignalsMixin, TestDataMixin, TransactionTestCase):
    """
    Concurrency test for SubscriptionCreateSerializer.
    Ensures no duplicate emails and safe threaded operations with signals disabled.
    """
    reset_sequences = True

    def setUp(self):
        self.user1 = self.get_or_create_user("user1@example.com", "Investor", "One")
        self.user2 = self.get_or_create_user("user2@example.com", "Investor", "Two")
        self.user3 = self.get_or_create_user()  # random unique email

        self.setup_industries()
        self.setup_locations()

        self.startup1 = self.get_or_create_startup(
            user=self.user1,
            industry=self.industry,
            company_name="Fintech Solutions",
            location=self.startup_location
        )

        self.investor1 = self.get_or_create_investor(self.user1, "Investor One", Stage.MVP, Decimal("1000000.00"))
        self.investor2 = self.get_or_create_investor(self.user2, "Investor Two", Stage.MVP, Decimal("2000000.00"))
        self.investor3 = self.get_or_create_investor(self.user3, "Investor Three", Stage.MVP, Decimal("500000.00"))

        self.setup_category()
        self.project1 = self.get_or_create_project(
            startup=self.startup1,
            category=self.category,
            title="First Test Project",
            funding_goal=Decimal("1000.00")
        )

    def test_concurrent_subscriptions(self):
        amount1 = Decimal("600.00")
        amount2 = Decimal("500.00")
        errors = []

        def subscribe(investor, amount, delay=0):
            close_old_connections()
            time.sleep(delay)
            data = self.get_subscription_data(investor, self.project1, amount)
            serializer = SubscriptionCreateSerializer(data=data)
            try:
                with transaction.atomic():
                    Project.objects.select_for_update().get(pk=self.project1.pk)
                    if serializer.is_valid(raise_exception=True):
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
