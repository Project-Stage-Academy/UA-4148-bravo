from django_elasticsearch_dsl import Document, Index
from django_elasticsearch_dsl.registries import registry
from .models import Startup

startup_index = Index('startups')

@registry.register_document
class StartupDocument(Document):
    class Index:
        name = 'startups'

    class Django:
        model = Startup
        fields = [
            'company_name',
            'description',
            'funding_stage',
            'location',
            'industries',
        ]
