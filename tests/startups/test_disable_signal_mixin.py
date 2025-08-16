# tests/startups/test_disable_signal_mixin.py
"""
Mixin to disable Elasticsearch indexing during tests.
All updates and deletes from django-elasticsearch-dsl become no-ops.
This avoids real Elasticsearch connection attempts.
"""

from unittest.mock import patch
import atexit

# Patch registry.update and registry.delete globally for this module
update_patcher = patch(
    "django_elasticsearch_dsl.registries.registry.update",
    lambda *args, **kwargs: None
)
delete_patcher = patch(
    "django_elasticsearch_dsl.registries.registry.delete",
    lambda *args, **kwargs: None
)

# Start patch immediately at import time
update_patcher.start()
delete_patcher.start()

# Ensure patch stops when Python exits
atexit.register(update_patcher.stop)
atexit.register(delete_patcher.stop)


class DisableElasticsearchSignalsMixin:
    """
    Base mixin for test cases to ensure Elasticsearch signals do nothing.
    This allows creation of model instances without connecting to Elasticsearch.
    """
    pass

