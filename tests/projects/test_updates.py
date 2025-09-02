from django.urls import reverse
from rest_framework import status
from tests.test_base_case import BaseAPITestCase
from projects.models import ProjectHistory
from communications.models import Notification

class ProjectUpdateAPITests(BaseAPITestCase):

    def setUp(self):
        super().setUp()
        self.project = self.get_or_create_project(startup=self.startup)
        self.client.force_authenticate(user=self.startup_user)
        self.url = f"/api/v1/projects/{self.project.pk}/"

    def test_project_update_creates_history(self):
        """We verify that the update creates an entry in ProjectHistory."""
        self.assertEqual(ProjectHistory.objects.count(), 0)
        
        update_data = {'title': 'A Brand New Title'}
        response = self.client.patch(self.url, update_data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ProjectHistory.objects.count(), 1)
        
        history = ProjectHistory.objects.first()
        self.assertEqual(history.project, self.project)
        self.assertEqual(history.user, self.startup_user)
        self.assertIn('title', history.changed_fields)
        self.assertEqual(history.changed_fields['title']['new'], 'A Brand New Title')

    def test_project_update_triggers_notification(self):
        """We verify that the update sends notifications to subscribed investors."""
        self.get_or_create_subscription(self.investor1, self.project, 100)
        self.assertEqual(Notification.objects.count(), 0)
        
        update_data = {'description': 'An updated description for investors.'}
        self.client.patch(self.url, update_data, format="json")

        notifications = Notification.objects.filter(
            user=self.investor1.user, 
            related_project_id=self.project.id
        )
        self.assertEqual(notifications.count(), 1)
        notification = notifications.first()
        self.assertEqual(notification.notification_type.code, 'project_updated')