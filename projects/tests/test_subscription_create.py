# import pytest
# from decimal import Decimal
# from django.urls import reverse
# from rest_framework.test import APIClient
# from rest_framework import status

# from users.models import User, UserRole
# from profiles.models import Industry, Location, Startup, Investor
# from projects.models import Project, Category
# from investments.models import Subscription

# @pytest.fixture
# def api_client(db):
#     """Fixture to create an APIClient instance."""
#     return APIClient()

# @pytest.fixture
# def investor_user(db):
#     """Creates a user with the 'investor' role."""
#     role_investor, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER, defaults={'role': 'investor'})
#     return User.objects.create_user(
#         email="investor@example.com",
#         password="testpassword123",
#         first_name="Test",
#         last_name="Investor",
#         role=role_investor
#     )

# @pytest.fixture
# def startup_user(db):
#     """Creates a user with the 'user' role (startup owner)."""
#     role_user, _ = UserRole.objects.get_or_create(role=UserRole.Role.USER)
#     return User.objects.create_user(
#         email="startup_owner@example.com",
#         password="testpassword123",
#         first_name="Startup",
#         last_name="Owner",
#         role=role_user
#     )

# @pytest.fixture
# def project_and_owner(db, startup_user):
#     """Creates a startup, a project, and returns the project and its owner."""
#     industry = Industry.objects.create(name="Technology")
#     location = Location.objects.create(country="US", city="Test City")
    
#     startup = Startup.objects.create(
#         user=startup_user,
#         industry=industry,
#         company_name="Startup Inc",
#         location=location,
#         email="startup@example.com",
#         founded_year=2020,
#         team_size=5,
#         stage="mvp"
#     )
#     category = Category.objects.create(name="Fintech")
#     project = Project.objects.create(
#         startup=startup,
#         title="Funding Project",
#         funding_goal=Decimal("1000.00"),
#         current_funding=Decimal("0.00"),
#         category=category,
#         email="project@example.com"
#     )
#     return project, startup_user


# @pytest.mark.django_db
# class TestSubscriptionCreateAPI:
#     """Groups all tests for the subscription creation endpoint."""

#     def test_create_subscription_success(self, api_client, investor_user, project_and_owner):
#         """Tests the successful creation of a subscription by an investor."""
#         project, _ = project_and_owner
#         api_client.force_authenticate(user=investor_user)
#         url = reverse("subscription-create")

#         payload = {"project": project.id, "amount": 200}
#         response = api_client.post(url, payload, format="json")

#         assert response.status_code == status.HTTP_201_CREATED
#         project.refresh_from_db()
#         assert project.current_funding == Decimal("200.00")
#         assert response.data["remaining_funding"] == Decimal("800.00")
#         assert response.data["project_status"] == "Partially funded"
#         assert Subscription.objects.count() == 1

#     def test_create_subscription_fully_funded(self, api_client, investor_user, project_and_owner):
#         """Tests that the project gets a 'Fully funded' status upon reaching its goal."""
#         project, _ = project_and_owner
#         project.current_funding = Decimal("900.00")
#         project.save()

#         api_client.force_authenticate(user=investor_user)
#         url = reverse("subscription-create")

#         payload = {"project": project.id, "amount": 100}
#         response = api_client.post(url, payload, format="json")

#         assert response.status_code == status.HTTP_201_CREATED
#         project.refresh_from_db()
#         assert project.current_funding == Decimal("1000.00")
#         assert response.data["project_status"] == "Fully funded"

#     def test_create_subscription_exceeds_goal_fails(self, api_client, investor_user, project_and_owner):
#         """Tests that an investment exceeding the goal is blocked by validation."""
#         project, _ = project_and_owner
#         api_client.force_authenticate(user=investor_user)
#         url = reverse("subscription-create")

#         payload = {"project": project.id, "amount": 1500}
#         response = api_client.post(url, payload, format="json")

#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert "exceeds the remaining funding" in str(response.data)
#         assert Subscription.objects.count() == 0

#     def test_unauthenticated_user_cannot_subscribe(self, api_client, project_and_owner):
#         """Tests that an unauthenticated user cannot invest."""
#         project, _ = project_and_owner
#         url = reverse("subscription-create")
#         payload = {"project": project.id, "amount": 200}
#         response = api_client.post(url, payload, format="json")

#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#         assert Subscription.objects.count() == 0

#     def test_non_investor_cannot_subscribe(self, api_client, startup_user, project_and_owner):
#         """
#         Test: Checks that an authenticated user without the 'investor' role cannot invest.
#         This verifies the IsInvestor permission class.
#         """
#         project, _ = project_and_owner
#         api_client.force_authenticate(user=startup_user)
#         url = reverse("subscription-create")

#         payload = {"project": project.id, "amount": 100}
#         response = api_client.post(url, payload, format="json")

#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert Subscription.objects.count() == 0

#     def test_startup_owner_cannot_invest_in_own_project(self, api_client, project_and_owner):
#         """
#         Test: Checks the validation that prevents a startup owner from investing in their own project.
#         Important: for this test, the project owner must also have the investor role.
#         """
#         project, owner = project_and_owner
        
#         investor_role, _ = UserRole.objects.get_or_create(role='investor')
#         owner.role = investor_role
#         owner.save()
#         Investor.objects.create(
#             user=owner,
#             industry=project.startup.industry,
#             company_name="Owner As Investor",
#             location=project.startup.location,
#             email="owner_as_investor@example.com",
#             founded_year=2021
#         )

#         api_client.force_authenticate(user=owner)
#         url = reverse("subscription-create")

#         payload = {"project": project.id, "amount": 100}
#         response = api_client.post(url, payload, format="json")
        
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert "You cannot invest in your own project" in str(response.data)
#         assert Subscription.objects.count() == 0

#     def test_invest_in_already_fully_funded_project_fails(self, api_client, investor_user, project_and_owner):
#         """
#         Test: Checks that it's not possible to invest in a project that is already 100% funded.
#         """
#         project, _ = project_and_owner
#         project.current_funding = project.funding_goal
#         project.save()
        
#         api_client.force_authenticate(user=investor_user)
#         url = reverse("subscription-create")

#         payload = {"project": project.id, "amount": 50}
#         response = api_client.post(url, payload, format="json")

#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert "project is already fully funded" in str(response.data)
#         assert Subscription.objects.count() == 0

#     def test_invest_with_invalid_amount_fails(self, api_client, investor_user, project_and_owner):
#         """Test: Checks validation for a zero or negative investment amount."""
#         project, _ = project_and_owner
#         api_client.force_authenticate(user=investor_user)
#         url = reverse("subscription-create")

#         payload_zero = {"project": project.id, "amount": 0}
#         response_zero = api_client.post(url, payload_zero, format="json")
#         assert response_zero.status_code == status.HTTP_400_BAD_REQUEST
        
#         payload_negative = {"project": project.id, "amount": -100}
#         response_negative = api_client.post(url, payload_negative, format="json")
#         assert response_negative.status_code == status.HTTP_400_BAD_REQUEST
        
#         assert Subscription.objects.count() == 0

#     def test_invest_in_nonexistent_project_fails(self, api_client, investor_user):
#         """Test: Checks that a request with a non-existent project ID returns a 400 error."""
#         api_client.force_authenticate(user=investor_user)
#         url = reverse("subscription-create")
        
#         non_existent_project_id = 9999
#         payload = {"project": non_existent_project_id, "amount": 100}
#         response = api_client.post(url, payload, format="json")

#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert "Invalid pk" in str(response.data['project'])