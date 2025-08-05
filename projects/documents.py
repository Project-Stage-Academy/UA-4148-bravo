from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from projects.models import Project

@registry.register_document
class ProjectDocument(Document):
    startup_name = fields.TextField(attr='startup.company_name')
    required_amount = fields.FloatField(attr='required_amount')

    class Index:
        name = 'projects'
        settings = {'number_of_shards': 1, 'number_of_replicas': 0}

    class Django:
        model = Project
        fields = ['title', 'description', 'status']

    def get_queryset(self):
        return super().get_queryset().select_related('startup')

    def get_indexing_queryset(self):
        return self.get_queryset().iterator(chunk_size=5000)