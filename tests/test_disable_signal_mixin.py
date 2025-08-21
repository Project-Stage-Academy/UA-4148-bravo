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
        super().setUpClass()

        # Disconnect signals to prevent automatic indexing
        post_save.disconnect(update_startup_document, sender=Startup)
        post_delete.disconnect(delete_startup_document, sender=Startup)

        # Patch update/delete methods of all relevant documents
        cls.startup_update_patcher = patch.object(StartupDocument, 'update', return_value=None)
        cls.startup_delete_patcher = patch.object(StartupDocument, 'delete', return_value=None)
        cls.project_update_patcher = patch.object(ProjectDocument, 'update', return_value=None)
        cls.project_delete_patcher = patch.object(ProjectDocument, 'delete', return_value=None)

        cls.mock_startup_update = cls.startup_update_patcher.start()
        cls.mock_startup_delete = cls.startup_delete_patcher.start()
        cls.mock_project_update = cls.project_update_patcher.start()
        cls.mock_project_delete = cls.project_delete_patcher.start()

        # Create test data after disabling signals and patching documents
        if hasattr(cls, "setup_all"):
            cls.setup_all()

    @classmethod
    def tearDownClass(cls):
        # Stop all active patches
        cls.startup_update_patcher.stop()
        cls.startup_delete_patcher.stop()
        cls.project_update_patcher.stop()
        cls.project_delete_patcher.stop()

        # Reconnect signals after tests
        post_save.connect(update_startup_document, sender=Startup)
        post_delete.connect(delete_startup_document, sender=Startup)

        # Call parent tearDownClass if defined
        super_method = getattr(super(), "tearDownClass", None)
        if super_method:
            super_method()


















