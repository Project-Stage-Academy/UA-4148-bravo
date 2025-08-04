from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User

@receiver(post_save, sender=User)
def handle_user_created(sender, instance, created, **kwargs):
    """
    Handle post-save signal for the User model.

    Sends a welcome message or performs other actions when a new user is created.
    Logs updates when an existing user is modified.

    Args:
        sender (Model): The model class.
        instance (User): The saved user instance.
        created (bool): Whether this was a creation or an update.
        **kwargs: Additional signal parameters.
    """
    
    if created:
        print(f"[SIGNAL] New user created: {instance.email}")
    else:
        print(f"[SIGNAL] User updated: {instance.email}")