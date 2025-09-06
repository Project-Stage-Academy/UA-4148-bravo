from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from startups.models import Startup, Industry, Location

User = get_user_model()


class StartupCatalogAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # users
        self.owner = User.objects.create_user(email="owner@example.com", password="pass")
        self.viewer = User.objects.create_user(email="viewer@example.com", password="pass")
        self.other_owner = User.objects.create_user(email="other@example.com", password="pass")

        # authenticate viewer (catalog available only for authenticated users)
        self.client.force_authenticate(self.viewer)

        # reference data
        self.ind_fin = Industry.objects.create(name="Fintech")
        self.ind_ai = Industry.objects.create(name="AI")

        self.loc_kyiv = Location.objects.create(country="UA", city="Kyiv")
        self.loc_lviv = Location.objects.create(country="UA", city="Lviv")

        # Data
        # public startup owned by another user — should be visible to all authenticated users
        self.pub = Startup.objects.create(
            user=self.owner,
            company_name="Acme",
            industry=self.ind_fin,          
            location=self.loc_kyiv,
            website="https://ac.me",
            email="acme@example.com",
            founded_year=2024,
            team_size=10,
            funding_needed=Decimal("500000.00"),
            stage="mvp",                   
            is_public=True,
            is_verified=True,
        )

        # private startup of the current user — should also be visible (because it is owned by me)
        self.my_private = Startup.objects.create(
            user=self.viewer,
            company_name="MyPrivate",
            industry=self.ind_ai,
            location=self.loc_lviv,
            website="https://me.example",
            email="me@example.com",
            founded_year=2024,
            team_size=3,
            funding_needed=Decimal("10000.00"),
            stage="idea",
            is_public=False,                # private
            is_verified=False,
        )

        # private startup of another user — should NOT be visible
        self.other_private = Startup.objects.create(
            user=self.other_owner,
            company_name="Hidden",
            industry=self.ind_ai,
            location=self.loc_lviv,
            website="https://hidden.example",
            email="hidden@example.com",
            founded_year=2023,
            team_size=7,
            funding_needed=Decimal("20000.00"),
            stage="idea",
            is_public=False,              
            is_verified=True,
        )

        # base URLs via reverse (names from DRF router)
        self.list_url = reverse("startup-list")                 # /api/v1/startups/
        self.detail_url = lambda pk: reverse("startup-detail", args=[pk])  # /api/v1/startups/{id}/

    # ---------- PERMISSIONS ----------
    def test_list_requires_auth(self):
        client = APIClient()  
        resp = client.get(self.list_url)
        self.assertIn(resp.status_code, (401, 403))

    def test_detail_requires_auth(self):
        client = APIClient() 
        resp = client.get(self.detail_url(self.pub.id))
        self.assertIn(resp.status_code, (401, 403))

    # ---------- LIST / VISIBILITY ----------
    def test_list_includes_public_and_my_private(self):
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, 200)
        ids = {item["id"] for item in resp.data}
        self.assertIn(self.pub.id, ids)            
        self.assertIn(self.my_private.id, ids)    
        self.assertNotIn(self.other_private.id, ids) 

    # ---------- FILTERS ----------
    def test_filter_by_industry_name(self):
        resp = self.client.get(self.list_url, {"industry": "Fintech"})
        self.assertEqual(resp.status_code, 200)
        ids = {item["id"] for item in resp.data}
        self.assertIn(self.pub.id, ids)
        self.assertNotIn(self.my_private.id, ids) 

    def test_filter_by_min_team_size(self):
        resp = self.client.get(self.list_url, {"min_team_size": 5})
        self.assertEqual(resp.status_code, 200)
        ids = {item["id"] for item in resp.data}
        self.assertIn(self.pub.id, ids)         
        # my private startup has team_size=3 -> should be filtered out
        self.assertNotIn(self.my_private.id, ids)

    def test_filter_by_funding_needed_lte(self):
        # limit 20k leaves only those with funding_needed <= 20000
        resp = self.client.get(self.list_url, {"funding_needed__lte": 20000})
        self.assertEqual(resp.status_code, 200)
        ids = {item["id"] for item in resp.data}
        self.assertIn(self.my_private.id, ids)    
        self.assertNotIn(self.pub.id, ids)       

    def test_filter_by_country_and_city(self):
        # pub -> UA, Kyiv; my_private -> UA, Lviv
        resp = self.client.get(self.list_url, {"country": "UA", "city": "Kyiv"})
        self.assertEqual(resp.status_code, 200)
        ids = {item["id"] for item in resp.data}
        self.assertIn(self.pub.id, ids)
        self.assertNotIn(self.my_private.id, ids)

    def test_filter_by_is_verified(self):
        resp = self.client.get(self.list_url, {"is_verified": True})
        self.assertEqual(resp.status_code, 200)
        ids = {item["id"] for item in resp.data}
        self.assertIn(self.pub.id, ids)           
        self.assertNotIn(self.my_private.id, ids)  

    # ---------- DETAIL ----------
    def test_detail_returns_object(self):
        resp = self.client.get(self.detail_url(self.pub.id))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["id"], self.pub.id)
        # basic fields
        self.assertEqual(resp.data["company_name"], "Acme")
        self.assertIn("industry", resp.data)
        self.assertIn("location", resp.data)

    # ---------- SEARCH (optional, if ES is running) ----------
    # For a stable test without ES — can skip or accept (200 or 503)
    def test_search_endpoint_reachable(self):
        url = reverse("startups-search-list")
        resp = self.client.get(url, {"search": "Acme"})
        self.assertIn(resp.status_code, (200, 503))
