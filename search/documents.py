from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from startups.models import Startup
from projects.models import Project


@registry.register_document
class StartupDocument(Document):
    company_name = fields.TextField()
    description = fields.TextField()
    stage = fields.KeywordField()

    class Index:
        name = 'startups'
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Startup
        fields = ["id"]
        related_models = []

    def get_queryset(self):
        return super().get_queryset().select_related("user")


@registry.register_document
class ProjectDocument(Document):
    title = fields.TextField()
    description = fields.TextField()
    status = fields.KeywordField()
    funding_goal = fields.FloatField()

    class Index:
        name = 'projects'
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = Project
        fields = ["id", "website"]
        related_models = []

    def get_queryset(self):
        return super().get_queryset().select_related("startup")
