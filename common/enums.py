from django.db.models import TextChoices


class Stage(TextChoices):
    IDEA = 'idea', 'Idea'
    MVP = 'mvp', 'MVP'
    LAUNCH = 'launch', 'Launch'
    SCALE = 'scale', 'Scale'
    EXIT = 'exit', 'Exit'


class ProjectStatus(TextChoices):
    DRAFT = 'draft', 'Draft'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
