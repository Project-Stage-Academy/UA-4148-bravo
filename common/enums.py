from django.db.models import TextChoices


class Stage(TextChoices):
    """
    Represents the lifecycle stage of a startup or company.

    Stages:
    - IDEA: Initial concept phase
    - MVP: Minimum Viable Product developed
    - LAUNCH: Public release, product is live
    - SCALE: Growth phase, expanding user base or market
    - EXIT: Final stage — acquisition, IPO, or shutdown
    """
    IDEA = 'idea', 'Idea'
    MVP = 'mvp', 'MVP'
    LAUNCH = 'launch', 'Launch'
    SCALE = 'scale', 'Scale'
    EXIT = 'exit', 'Exit'

    def display(self):
        """
        Returns the human-readable label of the current stage.
        """
        return self.label


class ProjectStatus(TextChoices):
    """
    Indicates the current status of a project.

    Statuses:
    - DRAFT: Initial draft, not yet active
    - IN_PROGRESS: Actively being worked on
    - COMPLETED: Finished and delivered
    - CANCELLED: Terminated before completion
    """
    DRAFT = 'draft', 'Draft'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
