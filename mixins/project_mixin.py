from projects.models import Project, Category
from decimal import Decimal


class ProjectMixin:
    """
    Mixin class providing setup and utility methods for creating Project and Category instances
    used in testing scenarios.

    Assumes the consuming test class provides a `startup` attribute for linking Projects.
    """

    @classmethod
    def create_project(cls, title="Test Project", funding_goal="10000.00", **kwargs):
        """
        Create and return a new Project instance with default or provided attributes.

        This method also creates a Category instance linked to the Project.

        Args:
            title (str, optional): Title of the project. Defaults to "Test Project".
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
        """
        Create a project and associated category, then verify their creation.

        Assigns the created Project instance to `cls.project` and
        the Category instance to `cls.category`.
        """
        cls.project = cls.create_project()

        assert Category.objects.filter(name=cls.category.name).exists(), "Category not created"
        assert Project.objects.filter(title=cls.project.title).exists(), "Project not created"

    @classmethod
    def setup_all(cls):
        """
        Perform all setup steps related to Projects and Categories.
        """
        cls.setup_project()

    @classmethod
    def tear_down(cls):
        """
        Clean up Project and Category instances created during tests.
        Deletes the project referenced by `cls.project` and category referenced by `cls.category`.
        """
        if hasattr(cls, 'project'):
            Project.objects.filter(pk=cls.project.pk).delete()

        if hasattr(cls, 'category'):
            Category.objects.filter(pk=cls.category.pk).delete()
