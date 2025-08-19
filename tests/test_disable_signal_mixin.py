from django.db.models.signals import post_save, post_delete
from startups.models import Startup
from startups.signals import update_startup_document, delete_startup_document
from unittest.mock import patch

# Import all Elasticsearch documents that may be triggered during test data creation
from startups.documents import StartupDocument
from projects.documents import ProjectDocument
# Add other documents here if needed:
# from investors.documents import InvestorDocument
# from investments.documents import SubscriptionDocument

class DisableElasticsearchSignalsMixin:
    """
    Mixin to disable Elasticsearch indexing during tests.
    Disconnects Django signals and mocks update/delete methods of all registered documents.
    """

    @classmethod
    def setUpClass(cls):
        # Disconnect signals to prevent automatic indexing
        post_save.disconnect(update_startup_document, sender=Startup)
        post_delete.disconnect(delete_startup_document, sender=Startup)

        # Patch update/delete methods of all relevant documents
        cls.es_patchers = [
            patch.object(StartupDocument, 'update', lambda self, instance, **kwargs: None),
            patch.object(StartupDocument, 'delete', lambda self, instance, **kwargs: None),
            patch.object(ProjectDocument, 'update', lambda self, instance, **kwargs: None),
            patch.object(ProjectDocument, 'delete', lambda self, instance, **kwargs: None),
            # Add more patchers here if needed
        ]

        for patcher in cls.es_patchers:
            patcher.start()

        # Create test data after disabling signals and patching documents
        if hasattr(cls, "setup_all"):
            cls.setup_all()

        # Call parent setUpClass if defined
        super_method = getattr(super(), "setUpClass", None)
        if super_method:
            super_method()

    @classmethod
    def tearDownClass(cls):
        # Stop all active patches
        for patcher in getattr(cls, "es_patchers", []):
            try:
                patcher.stop()
            except Exception:
                pass

        # Reconnect signals after tests
        post_save.connect(update_startup_document, sender=Startup)
        post_delete.connect(delete_startup_document, sender=Startup)

        # Call parent tearDownClass if defined
        super_method = getattr(super(), "tearDownClass", None)
        if super_method:
            super_method()


















