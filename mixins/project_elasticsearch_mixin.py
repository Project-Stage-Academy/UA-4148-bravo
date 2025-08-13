from tests.elasticsearch.factories import UserFactory, IndustryFactory, LocationFactory, StartupFactory, \
    CategoryFactory, ProjectFactory


class ProjectTestSetupMixin:
    @classmethod
    def setup(cls):
        cls.user1 = UserFactory()
        cls.user2 = UserFactory()
        cls.industry1 = IndustryFactory(name="Fintech")
        cls.industry2 = IndustryFactory(name="E-commerce")
        cls.location1 = LocationFactory(country="US")
        cls.location2 = LocationFactory(country="DE")
        cls.startup1 = StartupFactory(user=cls.user1, industry=cls.industry1, location=cls.location1,
                                      company_name="Fintech Solutions")
        cls.startup2 = StartupFactory(user=cls.user2, industry=cls.industry2, location=cls.location2,
                                      company_name="ShopFast")
        cls.category1 = CategoryFactory(name="Tech")
        cls.category2 = CategoryFactory(name="Finance")
        cls.project1 = ProjectFactory(startup=cls.startup1, category=cls.category1, title="First Test Project")
        cls.project2 = ProjectFactory(startup=cls.startup2, category=cls.category2, title="Second Test Project")
