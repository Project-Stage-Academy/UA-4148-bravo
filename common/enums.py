from django.db.models import TextChoices

class Stage(TextChoices):
    """
    Enumeration of the typical lifecycle stages of a startup or project.
    Used to track progress and determine applicable business logic.
    """

    IDEA = 'idea', 'Idea'  # Initial concept, not yet validated or developed
    MVP = 'mvp', 'MVP'  # Minimum viable product, basic version for early feedback
    PROTOTYPE = 'prototype', 'Prototype'  # Functional prototype, limited testing
    LAUNCH = 'launch', 'Launch'  # Public release, product is live
    SCALE = 'scale', 'Scale'  # Growth phase, expanding user base or market
    EXIT = 'exit', 'Exit'  # Final stage: acquisition, IPO, or shutdown

