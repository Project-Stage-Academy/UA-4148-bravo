from django.db.models.signals import post_save
from django.test import TestCase

from startups.signals import update_startup_document
from users.models import User


class BaseUserTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        post_save.disconnect(update_startup_document, sender=User)

    @classmethod
    def tearDownClass(cls):
        post_save.connect(update_startup_document, sender=User)
        super().tearDownClass()
