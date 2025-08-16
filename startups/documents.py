from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

# Import all models used in this document at the module level
# so they are available both inside the class and in Django's inner classes
from startups.models import Startup, Industry, Location


@registry.register_document
class StartupDocument(Document):
    """
    Elasticsearch document for indexing Startup model.
    Includes nested fields for Industry and Location.
    """

    # Nested industry fields for indexing related Industry model data
    industry = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.KeywordField(),
    })

    # Nested location fields for indexing related Location model data
    location = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'country': fields.KeywordField(),
        'region': fields.KeywordField(),
        'city': fields.KeywordField(),
        'address_line': fields.TextField(),
        'postal_code': fields.KeywordField(),
    })

    # Main startup fields
    company_name = fields.TextField(fields={
        'raw': fields.KeywordField()  # Keyword field for sorting by exact value
    })
    funding_stage = fields.KeywordField()
    investment_needs = fields.TextField()
    company_size = fields.KeywordField()
    is_active = fields.BooleanField()

    class Index:
        """
        Elasticsearch index configuration.
        """
        name = 'startups'  # Index name in Elasticsearch
        settings = {
            'number_of_shards': 1,      # Single shard for small datasets
            'number_of_replicas': 0     # No replicas for development
        }

    class Django:
        """
        Django integration configuration.
        Defines which model to index and related models that should trigger reindexing.
        """
        model = Startup
        fields = [
            'id',
            'description',
            'website',
            'email',
            'founded_year',
            'team_size',
            'created_at',
            'updated_at',
        ]
        related_models = [Industry, Location]  # Trigger reindexing when these models change

    def get_instances_from_related(self, related_instance):
        """
        Return related Startup instances when Industry or Location instances are updated.
        This is used by django-elasticsearch-dsl to know which documents to update.
        """
        if isinstance(related_instance, Industry):
            return related_instance.startups.all()
        elif isinstance(related_instance, Location):
            return related_instance.startups.all()

    def prepare_location(self, instance):
        """
        Prepare location data for indexing in Elasticsearch.
        Returns a dictionary with the location fields.
        """
        location = instance.location
        if not location:
            return {}

        return {
            'id': location.id,
            'country': str(location.country) if location.country else None,
            'region': location.region,
            'city': location.city,
            'address_line': location.address_line,
            'postal_code': location.postal_code,
        }
