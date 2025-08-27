from users.models import UserRole
from users.tasks import send_welcome_oauth_email_task


def create_or_update_user(strategy, details, backend, user=None, *args, **kwargs):
    """
    Pipeline for custom logic after OAuth.
    """
    if user:
        first_name = details.get('first_name', '')
        last_name = details.get('last_name', '')
        updated = False
        if first_name and user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if last_name and user.last_name != last_name:
            user.last_name = last_name
            updated = True
        if updated:
            user.save()
    else:
        user = strategy.create_user(
            email=details.get('email'),
            first_name=details.get('first_name', ''),
            last_name=details.get('last_name', ''),
            role=UserRole.objects.get(role='user')
        )
        send_welcome_oauth_email_task.delay(
            subject="Welcome!",
            message="Thanks for signing up via OAuth",
            recipient_list=[user.email]
        )
    return {'user': user}
