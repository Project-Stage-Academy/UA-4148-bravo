from rest_framework.test import APITestCase
from rest_framework import status
from projects.models import Project, Category
from projects.documents import ProjectDocument
from startups.models import Startup
from django.urls import reverse
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl import Index
import time

class ProjectElasticsearchTests(APITestCase):
    def setUp(self):
        self.client = self.client
        self.index = Index('projects')
        self.index.create()
        self.index.mapping(ProjectDocument)
        
        self.category1 = Category.objects.create(name="Tech")
        self.category2 = Category.objects.create(name="Finance")
        self.startup1 = Startup.objects.create(company_name="InnovateCo")
        self.startup2 = Startup.objects.create(company_name="FinGrowth Inc.")

        self.project1 = Project.objects.create(
            title="Search Engine for Startups",
            description="A powerful search tool.",
            category=self.category1,
            startup=self.startup1,
            goals="Improve discovery."
        )
        self.project2 = Project.objects.create(
            title="Financial Dashboard",
            description="Real-time financial data.",
            category=self.category2,
            startup=self.startup2,
            goals="Provide analytics."
        )

        time.sleep(1) 

    def tearDown(self):
        self.index.delete()

    def test_empty_query_returns_all_projects(self):
        url = reverse('project-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_no_results_for_non_existent_title(self):
        url = reverse('project-list')
        response = self.client.get(url, {'search': 'nonexistent_project'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_combined_filters_work_correctly(self):
        url = reverse('project-list')
        response = self.client.get(url, {
            'category.name': 'Tech', 
            'startup.company_name': 'InnovateCo'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Search Engine for Startups")

    def test_invalid_filter_field_returns_bad_request(self):
        url = reverse('project-list')
        response = self.client.get(url, {'nonexistent_field': 'value'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)