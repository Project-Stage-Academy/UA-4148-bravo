from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry
from startups.models import Startup

@registry.register_document
class StartupDocument(Document):
    location = fields.TextField(attr='location')
    industries = fields.TextField(
        attr='industries_names',
        multi=True
    )
    
    class Index:
        name = 'startups'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    class Django:
        model = Startup
        fields = [
            'company_name',
            'description',
            'funding_stage',
        ]
        
    def get_queryset(self):
        return super().get_queryset().prefetch_related('industries')

    def get_indexing_queryset(self):
        return self.get_queryset().iterator(chunk_size=5000)

    def industries_names(self, obj):
        return [industry.name for industry in obj.industries.all()]