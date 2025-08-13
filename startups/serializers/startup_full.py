from projects.serializers import ProjectReadSerializer
from startups.serializers.startup_base import StartupBaseSerializer


class StartupSerializer(StartupBaseSerializer):
    """
    Full serializer with nested project details.
    """
    projects = ProjectReadSerializer(many=True, read_only=True)

    class Meta(StartupBaseSerializer.Meta):
        fields = StartupBaseSerializer.Meta.fields + ['projects']
        read_only_fields = StartupBaseSerializer.Meta.read_only_fields + ['projects']
