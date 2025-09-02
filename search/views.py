from rest_framework.generics import ListAPIView
from django_elasticsearch_dsl.search import Search
from elasticsearch_dsl.query import Q
from startups.models import Startup
from projects.models import Project
from .documents import StartupDocument, ProjectDocument
from .serializers import StartupSearchSerializer, ProjectSearchSerializer


class StartupSearchView(ListAPIView):
    serializer_class = StartupSearchSerializer

    def get_queryset(self):
        query = self.request.query_params.get("q", "")
        if not query:
            return Startup.objects.none()

        search = StartupDocument.search().query(
            Q("multi_match", query=query, fields=["company_name", "description", "stage"])
        )
        ids = [hit.id for hit in search]
        return Startup.objects.filter(id__in=ids)


class ProjectSearchView(ListAPIView):
    serializer_class = ProjectSearchSerializer

    def get_queryset(self):
        query = self.request.query_params.get("q", "")
        if not query:
            return Project.objects.none()

        search = ProjectDocument.search().query(
            Q("multi_match", query=query, fields=["title", "description", "status"])
        )
        ids = [hit.id for hit in search]
        return Project.objects.filter(id__in=ids)
