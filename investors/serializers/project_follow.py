from rest_framework import serializers
from django.db import transaction

from investors.models import ProjectFollow
from projects.models import Project
from investors.models import Investor


class ProjectFollowCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new project follow relationship.
    
    This serializer handles the creation of ProjectFollow instances when
    investors want to follow specific projects to receive notifications
    about project updates and milestones.
    
    Fields:
        investor (Investor): The investor following the project (read-only, set from request).
        project (Project): The project to follow (read-only, set from URL).
        followed_at (DateTime): Timestamp when the follow was created (read-only).
        is_active (Boolean): Whether the follow is active (read-only).
    
    Validation:
        - Ensures project exists and is valid.
        - Ensures the requesting user is an authenticated investor.
        - Prevents self-following (investor cannot follow their own startup's projects).
        - Prevents duplicate follows (handled by unique constraint).
    """
    
    class Meta:
        model = ProjectFollow
        fields = ["id", "investor", "project", "followed_at", "is_active"]
        read_only_fields = ["id", "investor", "project", "followed_at", "is_active"]

    def validate(self, data):
        """Validate the project follow creation request."""
        project = self.context.get("project")
        if not project:
            raise serializers.ValidationError({"project": "Project is required."})
            
        request = self.context.get("request")
        if not request or not hasattr(request, "user") or not hasattr(request.user, "investor"):
            raise serializers.ValidationError({"investor": "Authenticated investor required."})
            
        investor = request.user.investor
        startup = getattr(project, 'startup', None)
        if startup and getattr(investor, 'user', None) and getattr(startup, 'user', None):
            if investor.user.pk == startup.user.pk:
                raise serializers.ValidationError({
                    "non_field_errors": ["You cannot follow your own startup's projects."]
                })
        
        if ProjectFollow.objects.filter(investor=investor, project=project, is_active=True).exists():
            raise serializers.ValidationError({
                "non_field_errors": ["You are already following this project."]
            })
        
        return data

    def create(self, validated_data):
        """Create a new project follow relationship."""
        project = self.context.get("project")
        request = self.context.get("request")
        investor = request.user.investor
        
        with transaction.atomic():
            project_follow = ProjectFollow.objects.create(
                investor=investor,
                project=project,
                is_active=True
            )
            
        return project_follow


class ProjectFollowSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying project follow relationships.
    
    This serializer is used for listing and retrieving existing
    project follow relationships with related data.
    """
    investor_name = serializers.CharField(source='investor.company_name', read_only=True)
    investor_email = serializers.CharField(source='investor.user.email', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    project_description = serializers.CharField(source='project.description', read_only=True)
    startup_name = serializers.CharField(source='project.startup.company_name', read_only=True)
    
    class Meta:
        model = ProjectFollow
        fields = [
            "id", "investor", "project", "followed_at", "is_active",
            "investor_name", "investor_email", "project_title", 
            "project_description", "startup_name"
        ]
        read_only_fields = ["id", "followed_at"]


