from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from projects.models import Project
from projects.models import Category
from startups.models import Startup

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
        # Related models must be actual model classes, not strings
        related_models = [Startup, Category]

    def prepare_category(self, instance):
        if instance.category:
            return {
                'id': instance.category.id,
                'name': instance.category.name,
            }
        return {}

    def prepare_startup(self, instance):
        if instance.startup:
            return {
                'id': instance.startup.id,
                'company_name': instance.startup.company_name,
            }
        return {}

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, Category):
            return related_instance.project_set.all()
        elif isinstance(related_instance, Startup):
            return related_instance.projects.all()
        return []

