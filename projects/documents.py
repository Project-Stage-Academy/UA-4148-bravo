from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from projects.models import Project


@registry.register_document
class ProjectDocument(Document):
    category = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.KeywordField(),
    })
    startup = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'company_name': fields.KeywordField(),
    })

    class Index:
        name = 'projects'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Project
        fields = [
            'id',
            'title',
            'description',
            'status',
        ]
        related_models = ['startup', 'category']
