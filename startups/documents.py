from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from startups.models import Startup

@registry.register_document
class StartupDocument(Document):
    industries = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.KeywordField(),
    })
    location = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'country': fields.KeywordField(),
    })
    funding_stage = fields.KeywordField()

    class Index:
        name = 'startups'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Startup
        fields = [
            'id',
            'company_name',
            'description',
        ]
        related_models = ['industries', 'location']