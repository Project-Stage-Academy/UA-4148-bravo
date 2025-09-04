import requests
import logging
from users.models import UserRole
from users.tasks import send_welcome_oauth_email_task

logger = logging.getLogger(__name__)

def create_or_update_user(strategy, details, backend, user=None, *args, **kwargs):
    """
    Pipeline for custom logic after OAuth.
    """
    created = False
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
        created = True
        send_welcome_oauth_email_task.delay(
            subject="Welcome!",
            message="Thanks for signing up via OAuth",
            recipient_list=[user.email]
        )
    strategy.session_set('user_created', created)    
    return {'user': user}

def activate_verified_user(strategy, details, backend, user=None, *args, **kwargs):
    """
    Pipeline step to activate a user only if their email is verified via the OAuth provider.
    Supports Google and GitHub.
    """
    if not user or user.is_active:
        return {'user': user}

    verified_email = False
    response_data = kwargs.get('response', {})

    if backend.name == 'google-oauth2':
        verified_email = response_data.get('email_verified', False)

    elif backend.name == 'github':
        social = kwargs.get('social') or user.social_auth.filter(provider='github').first()
        if social and 'access_token' in social.extra_data:
            access_token = social.extra_data['access_token']
            headers = {
                'Authorization': f'token {access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            try:
                github_response = requests.get('https://api.github.com/user/emails', headers=headers, timeout=(3.05, 5))
                if github_response.status_code == 200:
                    emails = github_response.json()
                    for email_data in emails:
                        if email_data.get('verified') and email_data.get('primary'):
                            primary_email = email_data.get('email')
                            if primary_email and user.email != primary_email:
                                user.email = primary_email
                                user.save(update_fields=["email"])
                            verified_email = True
                            break
            except requests.RequestException as e:
                logger.warning(f"GitHub email verification failed: {e}")

    if verified_email:
        user.is_active = True
        user.save(update_fields=["is_active"])

    return {'user': user}

def safe_user_details(strategy, details, backend, user=None, *args, **kwargs):
    """
    Update user with provider details, but never touch first_name/last_name.
    Returns {'user': user} to keep the pipeline happy.
    """
    if user is None:
        return {'user': None}

    changed = False
    for field, value in details.items():
        if field in ['first_name', 'last_name']:
            continue
        if value is None:
            continue
        if hasattr(user, field):
            current_value = getattr(user, field)
            if current_value != value:
                setattr(user, field, value)
                changed = True

    if changed:
        user.save()

    return {'user': user} 