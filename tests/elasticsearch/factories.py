import factory
from decimal import Decimal
from django.contrib.auth import get_user_model
from projects.models import Project, Category
from startups.models import Startup, Industry, Location
from common.enums import Stage
from users.models import UserRole

User = get_user_model()


class UserRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserRole
        django_get_or_create = ('role',)  # <- ключ для get_or_create

    role = UserRole.Role.USER


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    role = factory.SubFactory(UserRoleFactory)  # завжди отримає існуючий або створить один раз
    first_name = "John"
    last_name = "Doe"
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall('set_password', 'password123')


class IndustryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Industry

    name = factory.Sequence(lambda n: f'Industry{n}')


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    country = "US"


class StartupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Startup

    user = factory.SubFactory(UserFactory)
    industry = factory.SubFactory(IndustryFactory)
    company_name = factory.Sequence(lambda n: f'Company{n}')
    description = "Description"
    location = factory.SubFactory(LocationFactory)
    email = factory.Sequence(lambda n: f'company{n}@example.com')
    founded_year = 2020
    team_size = 10
    stage = Stage.MVP


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Category{n}')


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    startup = factory.SubFactory(StartupFactory)
    title = factory.Sequence(lambda n: f'Project {n}')
    funding_goal = Decimal("10000.00")
    current_funding = Decimal("0.00")
    category = factory.SubFactory(CategoryFactory)
    email = factory.Sequence(lambda n: f'project{n}@example.com')
