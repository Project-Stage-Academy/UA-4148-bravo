from django.db.models import TextChoices


class Stage(TextChoices):
    """
    Represents the lifecycle stage of a startup or company.
    Each stage reflects a different phase of growth or transition.
    """
    IDEA = 'idea', 'Idea'               # Initial concept phase
    MVP = 'mvp', 'MVP'                  # Minimum Viable Product developed
    LAUNCH = 'launch', 'Launch'        # Public release, product is live
    SCALE = 'scale', 'Scale'           # Growth phase, expanding user base or market
    EXIT = 'exit', 'Exit'              # Final stage: acquisition, IPO, or shutdown

    def display(self):
        """
        Returns the human-readable label of the current stage.
        """
        return self.label


class ProjectStatus(TextChoices):
    """
    Indicates the current status of a project.
    Useful for tracking progress and workflow state.
    """
    DRAFT = 'draft', 'Draft'                   # Initial draft, not yet active
    IN_PROGRESS = 'in_progress', 'In Progress' # Actively being worked on
    COMPLETED = 'completed', 'Completed'       # Finished and delivered
    CANCELLED = 'cancelled', 'Cancelled'       # Terminated before completion
