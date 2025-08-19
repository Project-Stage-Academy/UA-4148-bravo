from django.db.models.signals import post_save, post_delete
from startups.models import Startup
from startups.signals import update_startup_document, delete_startup_document
from unittest.mock import patch

class DisableElasticsearchSignalsMixin:
    """
    Mixin to disable Elasticsearch-related signals during tests.
    Patches StartupDocument update and delete methods to avoid connection errors.
    """

    @classmethod
    def setUpClass(cls):
        # Disconnect real signal handlers to prevent ES updates
        post_save.disconnect(update_startup_document, sender=Startup)
        post_delete.disconnect(delete_startup_document, sender=Startup)

        # Patch Elasticsearch document methods to no-op
        cls.es_update_patcher = patch(
            "startups.documents.StartupDocument.update", lambda *a, **kw: None
        )
        cls.es_delete_patcher = patch(
            "startups.documents.StartupDocument.delete", lambda *a, **kw: None
        )
        cls.es_update_patcher.start()
        cls.es_delete_patcher.start()

        super_method = getattr(super(), "setUpClass", None)
        if super_method:
            super_method()

    @classmethod
    def tearDownClass(cls):
        # Stop the patches
        try:
            cls.es_update_patcher.stop()
            cls.es_delete_patcher.stop()
        except AttributeError:
            pass

        # Reconnect the real signal handlers
        post_save.connect(update_startup_document, sender=Startup)
        post_delete.connect(delete_startup_document, sender=Startup)

        super_method = getattr(super(), "tearDownClass", None)
        if super_method:
            super_method()
















