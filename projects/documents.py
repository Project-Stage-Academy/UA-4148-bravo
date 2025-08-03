from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from .models import Project

project_index = Index('projects')

@registry.register_document
class ProjectDocument(Document):
    class Index:
        name = 'projects'

    class Django:
        model = Project
        fields = [
            'title',
            'description',
            'status',
            'required_amount',
        ]

        related_models = ['startup']
