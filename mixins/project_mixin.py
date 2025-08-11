from projects.models import Project, Category
from decimal import Decimal


class ProjectMixin:
    @classmethod
    def create_project(cls, title="Test Project", funding_goal="10000.00", **kwargs):
        """
        Create and return a new Project instance with default attributes.

        Args:
            title (str, optional): Title of the project.
            funding_goal (str or Decimal, optional): Funding goal amount; default "10000.00".
            **kwargs: Additional fields to pass to Project creation.

        Returns:
            Project: Newly created Project instance.
        """
        cls.category = Category.objects.create(name="FinTech")
        return Project.objects.create(
            startup=cls.startup,
            title=title,
            funding_goal=Decimal(funding_goal),
            current_funding=Decimal("0.00"),
            category=cls.category,
            email=f"{title.lower().replace(' ', '')}@example.com",
            **kwargs
        )

    @classmethod
    def setup_project(cls):
        cls.project = cls.create_project()

        assert Category.objects.filter(name=cls.category.name).exists(), "Category not created"
        assert Project.objects.filter(title=cls.project.title).exists(), "Project not created"

    @classmethod
    def setup_all(cls):
        cls.setup_project()
