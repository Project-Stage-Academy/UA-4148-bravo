from django.db.models import TextChoices

class Stage(TextChoices):
    IDEA = 'idea', 'Idea'
    MVP = 'mvp', 'MVP'
    PROTOTYPE = 'prototype', 'Prototype'
    LAUNCH = 'launch', 'Launch'
    SCALE = 'scale', 'Scale'
    EXIT = 'exit', 'Exit'
