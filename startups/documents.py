from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from startups.models import Startup


@registry.register_document
class StartupDocument(Document):

    industry = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.KeywordField(),
    })

    location = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'country': fields.KeywordField(),
        'region': fields.KeywordField(),
        'city': fields.KeywordField(),
        'address_line': fields.TextField(),
        'postal_code': fields.KeywordField(),
    })

    stage = fields.KeywordField()

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
            'website',
            'email',
            'founded_year',
            'team_size',
            'created_at',
            'updated_at',
        ]
        related_models = [Startup.industry.field.related_model, Startup.location.field.related_model]

    def prepare_industry(self, instance):
        if instance.industry:
            return {
                'id': instance.industry.id,
                'name': instance.industry.name,
            }
        return {}

    def prepare_location(self, instance):
        if instance.location:
            loc = instance.location
            return {
                'id': loc.id,
                'country': str(loc.country),
                'region': loc.region,
                'city': loc.city,
                'address_line': loc.address_line,
                'postal_code': loc.postal_code,
            }
        return {}

    def get_instances_from_related(self, related_instance):
        '''
        Given a related instance (Industry or Location),
        return the queryset of Startup instances that should be updated.
        '''
        if isinstance(related_instance, Startup.industry.field.related_model):
            return related_instance.startup_set.all()
        elif isinstance(related_instance, Startup.location.field.related_model):
            return related_instance.startup_set.all()
        return []
