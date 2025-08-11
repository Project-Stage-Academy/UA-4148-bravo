from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from startups.models import Startup, Industry, Location


@registry.register_document
class StartupDocument(Document):
    # Define nested Industry fields for indexing
    industry = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.KeywordField(),
    })

    # Define nested Location fields for indexing
    location = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'country': fields.KeywordField(),  # Store as string, not Country object
        'region': fields.KeywordField(),
        'city': fields.KeywordField(),
        'address_line': fields.TextField(),
        'postal_code': fields.KeywordField(),
    })

    company_name = fields.TextField(fields={
        'raw': fields.KeywordField()  # for sorting
    })

    funding_stage = fields.KeywordField()
    investment_needs = fields.TextField()
    company_size = fields.KeywordField()
    is_active = fields.BooleanField()

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
            'description',
            'website',
            'email',
            'founded_year',
            'team_size',
            'created_at',
            'updated_at',
        ]
        related_models = [Industry, Location]

    def get_instances_from_related(self, related_instance):
        """Ensure related model changes update the index."""
        if isinstance(related_instance, Industry):
            return related_instance.startups.all()
        elif isinstance(related_instance, Location):
            return related_instance.startups.all()

    def prepare_location(self, instance):
        """Prepare the location field for Elasticsearch indexing.

        Convert 'country' field from Country object to string code.
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
