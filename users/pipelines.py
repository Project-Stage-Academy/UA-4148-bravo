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
    return {'user': user}

def activate_verified_user(strategy, details, backend, user=None, *args, **kwargs):
    """
    Activate user only if email is verified. Critical security function.
    """
    if user and not user.is_active:
        verified_email = False
        response = kwargs.get('response', {})
        
        if backend.name == 'google-oauth2':
            verified_email = response.get('email_verified', False)
            
        elif backend.name == 'github':
            social = kwargs.get('social') or (
                user.social_auth.filter(provider='github').first() if user else None
                )        
            if social and social.extra_data:
                emails = social.extra_data.get('emails', []) 
                user_email = user.email or details.get('email', '')
                for email_data in emails:
                    if (isinstance(email_data, dict) and 
                        email_data.get('email') == user_email and 
                        email_data.get('verified', False)):
                        verified_email = True
                        break
            else:
                verified_email = True     
        if verified_email:
            user.is_active = True
            user.save()

def safe_user_details(strategy, details, backend, user=None, *args, **kwargs):
    """
    Update user with provider details, but never touch first_name/last_name.
    Returns {'user': user} to keep the pipeline happy.
    """
    if user is None:
        return

    changed = False
    for field, value in details.items():
        if field in ['first_name', 'last_name']:
            continue
        if not value:
            continue
        if hasattr(user, field):
            current_value = getattr(user, field)
            if current_value != value:
                setattr(user, field, value)
                changed = True

    if changed:
        user.save()

    return {'user': user} 