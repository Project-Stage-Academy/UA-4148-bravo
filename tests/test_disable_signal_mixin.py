from unittest.mock import patch
from django.db.models.signals import post_save, post_delete
from django.apps import apps

from startups.models import Startup
from startups.signals import update_startup_document, delete_startup_document
from startups.documents import StartupDocument
from projects.documents import ProjectDocument
from investments.signals import connect_signals
from investments.tasks import recalc_investment_shares_task
from django_elasticsearch_dsl.registries import registry


class DisableSignalsMixin:
    """
    Universal mixin to disable Elasticsearch and Celery signals during tests.
    - Disconnects startup signals from Elasticsearch
    - Disconnects investment signals from Celery
    - Patches ES update/delete and Celery task execution
    """

    @classmethod
    def setUpClass(cls):
        super_method = getattr(super(), "setUpClass", None)
        if super_method:
            super_method()

        # --- Disable startup Elasticsearch signals ---
        post_save.disconnect(update_startup_document, sender=Startup)
        post_delete.disconnect(delete_startup_document, sender=Startup)

        # Patch Elasticsearch registry.update to prevent actual ES requests
        cls.registry_patcher = patch.object(registry, "update", return_value=None)
        cls.mock_registry_update = cls.registry_patcher.start()

        # Patch Elasticsearch document methods
        cls.startup_update_patcher = patch.object(StartupDocument, "update", return_value=None)
        cls.startup_delete_patcher = patch.object(StartupDocument, "delete", return_value=None)
        cls.project_update_patcher = patch.object(ProjectDocument, "update", return_value=None)
        cls.project_delete_patcher = patch.object(ProjectDocument, "delete", return_value=None)

        cls.startup_update_patcher.start()
        cls.startup_delete_patcher.start()
        cls.project_update_patcher.start()
        cls.project_delete_patcher.start()

        # --- Disable investment signals (Celery) ---
        post_save.disconnect(dispatch_uid="update_investment_share_post_save")
        post_delete.disconnect(dispatch_uid="update_investment_share_post_delete")

        cls.recalc_task_patcher = patch.object(
            recalc_investment_shares_task, "delay", return_value=None
        )
        cls.recalc_task_patcher.start()

    @classmethod
    def tearDownClass(cls):
        # Stop all patches
        cls.registry_patcher.stop()
        cls.startup_update_patcher.stop()
        cls.startup_delete_patcher.stop()
        cls.project_update_patcher.stop()
        cls.project_delete_patcher.stop()
        cls.recalc_task_patcher.stop()

        # Reconnect startup signals
        post_save.connect(update_startup_document, sender=Startup)
        post_delete.connect(delete_startup_document, sender=Startup)

        # Reconnect investment signals
        connect_signals(apps=apps)

        super_method = getattr(super(), "tearDownClass", None)
        if super_method:
            super_method()






















