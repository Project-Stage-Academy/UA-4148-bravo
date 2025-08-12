from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from startups.models import Startup  # Global import only for model reference


# Elasticsearch document for indexing Startup model
@registry.register_document
class StartupDocument(Document):
    # Local imports used only for related_models and indexing logic
    from startups.models import Industry, Location

    # Nested industry fields
    industry = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.KeywordField(),
    })

    # Nested location fields
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
        'raw': fields.KeywordField()  # For sorting
    })
    funding_stage = fields.KeywordField()
    investment_needs = fields.TextField()
    company_size = fields.KeywordField()
    is_active = fields.BooleanField()

    # Elasticsearch index settings
    class Index:
        name = 'startups'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }

    # Django model and related configuration
    class Django:
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
        related_models = [Industry, Location]

    # Return affected startups when related models change
    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, self.Industry):
            return related_instance.startups.all()
        elif isinstance(related_instance, self.Location):
            return related_instance.startups.all()

    # Format location data for indexing
    def prepare_location(self, instance):
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
