from django.db.models.signals import post_save
from django.db.models.signals import post_migrate
from django.apps import apps
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
        
@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    """
    Creates default UserRole entries after migrations for the 'users' app.

    Args:
        sender: The app config that sent the signal.
        **kwargs: Additional signal arguments.
    """
    try:
        app_config = apps.get_app_config('users')
    except LookupError:
        return
    
    if sender.name == app_config.name:
        UserRole = apps.get_model(sender.label, 'UserRole')
        for role_value, _ in UserRole.Role.choices:
            UserRole.objects.get_or_create(role=role_value)