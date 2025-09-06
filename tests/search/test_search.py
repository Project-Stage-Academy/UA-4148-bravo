from decimal import Decimal
from unittest import mock

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from users.models import User, UserRole
from startups.models import Startup, Industry, Location
from projects.models import Project, Category

import search.views as sv


@override_settings(SECURE_SSL_REDIRECT=False)
class SearchTests(APITestCase):
    def setUp(self):
        # Role / user
        role_user, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            role=role_user,
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

        self.industry = Industry.objects.create(name="Healthcare")
        self.location = Location.objects.create(country="UA", city="Kyiv")
        self.category = Category.objects.create(name="Tech")

        # Startup
        self.startup = Startup.objects.create(
            user=self.user,
            company_name="Test Startup",
            description="AI Startup in healthcare",
            stage="seed",
            founded_year=2020,
            industry=self.industry,
            location=self.location,
            email="hello@test-startup.com",
            team_size=5,
        )

        changed = False
        for flag in ("is_active", "is_published", "is_verified", "published", "visible"):
            if hasattr(self.startup, flag) and not getattr(self.startup, flag):
                setattr(self.startup, flag, True)
                changed = True
        if changed:
            self.startup.save()

        # Project
        self.project = Project.objects.create(
            startup=self.startup,
            category=self.category,
            title="Health AI", 
            description="AI project for healthcare",
            status="active",   
            funding_goal=Decimal("10000.00"),
            current_funding=Decimal("0.00"),
            email="project@test-startup.com",
        )
        changed = False
        for flag in ("is_active", "is_published", "is_verified", "published", "visible"):
            if hasattr(self.project, flag) and not getattr(self.project, flag):
                setattr(self.project, flag, True)
                changed = True
        if changed:
            self.project.save()

    @staticmethod
    def _make_hit(doc_id):
        """ES hit supporting both hit.id and hit.meta.id access."""
        hit = mock.Mock()
        hit.id = str(doc_id)
        hit.meta = mock.Mock()
        hit.meta.id = str(doc_id)
        return hit

    def _chainable_search(self, search_obj, hits, qs=None):
        """
        Prepare a mocked search object compatible with the SUT:
          - iteration directly over search (for hit in search)
          - .query/.filter/.source/.extra return the same object
          - slicing [:N] returns the same object
          - .execute() also returns iterable(hits)
          - (optional) .to_queryset() -> qs
        """
        for m in ("query", "filter", "source", "extra"):
            getattr(search_obj, m).return_value = search_obj

        def _getitem(key):
            if isinstance(key, slice):
                return search_obj
            return hits[key]
        search_obj.__getitem__.side_effect = _getitem

        search_obj.__iter__.return_value = iter(hits)
        search_obj.__len__.return_value = len(hits)
        search_obj.__bool__.return_value = bool(hits)

        mock_resp = mock.MagicMock()
        mock_resp.__iter__.return_value = iter(hits)
        mock_resp.hits = hits
        search_obj.execute.return_value = mock_resp

        if qs is not None:
            search_obj.to_queryset.return_value = qs

    def test_startup_search_mocked(self):
        self.client.force_authenticate(user=self.user)
        with mock.patch.object(sv.StartupDocument, "search") as search_fn:
            search_obj = search_fn.return_value
            hit = self._make_hit(self.startup.id)
            qs = Startup.objects.filter(pk=self.startup.pk)
            self._chainable_search(search_obj, [hit], qs=qs)

            url = reverse("startup-search")
            query = "health"
            resp = self.client.get(url, {"q": query})
            self.assertTrue(search_fn.called, "StartupDocument.search() was not called (wrong patch target?)")
            self.assertEqual(resp.status_code, 200, resp.data)
            self.assertEqual(len(resp.data), 1, resp.data)
            self.assertEqual(resp.data[0]["company_name"], "Test Startup")

    def test_project_search_mocked(self):
        self.client.force_authenticate(user=self.user)
        with mock.patch.object(sv.ProjectDocument, "search") as search_fn:
            search_obj = search_fn.return_value
            hit = self._make_hit(self.project.id)
            qs = Project.objects.filter(pk=self.project.pk)
            self._chainable_search(search_obj, [hit], qs=qs)

            url = reverse("project-search")
            query = "health"
            resp = self.client.get(url, {"q": query})
            self.assertTrue(search_fn.called, "ProjectDocument.search() was not called (wrong patch target?)")
            self.assertEqual(resp.status_code, 200, resp.data)
            self.assertEqual(len(resp.data), 1, resp.data)
            self.assertEqual(resp.data[0]["title"], "Health AI") 

    def test_startup_search_empty_query(self):
        url = reverse("startup-search")
        resp = self.client.get(url, {"q": ""})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(len(resp.data), 0, resp.data)

    def test_project_search_empty_query(self):
        url = reverse("project-search")
        resp = self.client.get(url, {"q": ""})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(len(resp.data), 0, resp.data)
