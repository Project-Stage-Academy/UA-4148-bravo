import factory
from decimal import Decimal
from django.contrib.auth import get_user_model
import uuid

from investors.models import Investor
from projects.models import Project, Category
from startups.models import Startup, Industry, Location
from common.enums import Stage
from users.models import UserRole

User = get_user_model()


class UserRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserRole
        django_get_or_create = ('role',)

    role = UserRole.Role.USER


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    role = factory.SubFactory(UserRoleFactory)
    first_name = "John"
    last_name = "Doe"
    email = factory.Sequence(lambda n: f"user_{uuid.uuid4().hex[:8]}_{n}@example.com")
    password = factory.PostGenerationMethodCall('set_password', 'password123')
    is_active = True


class IndustryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Industry

    name = factory.Sequence(lambda n: f'Industry_{uuid.uuid4().hex[:8]}_{n}')


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    country = "US"


class StartupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Startup

    user = factory.SubFactory(UserFactory)
    industry = factory.SubFactory(IndustryFactory)
    company_name = factory.Sequence(lambda n: f'Startup_{uuid.uuid4().hex[:8]}_{n}')
    description = "Startup Description"
    location = factory.SubFactory(LocationFactory)
    email = factory.Sequence(lambda n: f'startup_{uuid.uuid4().hex[:8]}_{n}@example.com')
    founded_year = 2020
    team_size = 10
    stage = Stage.MVP


class InvestorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Investor

    user = factory.SubFactory(UserFactory)
    industry = factory.SubFactory(IndustryFactory)
    company_name = factory.Sequence(lambda n: f'Investor_{uuid.uuid4().hex[:8]}_{n}')
    description = "Investor Description"
    location = factory.SubFactory(LocationFactory)
    email = factory.Sequence(lambda n: f'investor_{uuid.uuid4().hex[:8]}_{n}@example.com')
    founded_year = 2000
    team_size = 50
    stage = Stage.MVP


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Category_{uuid.uuid4().hex[:8]}_{n}')


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    startup = factory.SubFactory(StartupFactory)
    title = factory.Sequence(lambda n: f'Project_{uuid.uuid4().hex[:8]}_{n}')
    funding_goal = Decimal("10000.00")
    current_funding = Decimal("0.00")
    category = factory.SubFactory(CategoryFactory)
    email = factory.Sequence(lambda n: f'project_{uuid.uuid4().hex[:8]}_{n}@example.com')
