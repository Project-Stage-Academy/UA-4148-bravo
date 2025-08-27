from django.core.cache import cache
from users.models import UserRole


def get_default_user_role():
    """
    Retrieve the default 'user' role with caching and error handling.

    Returns:
        UserRole: The default user role object

    Raises:
        RuntimeError: If the default user role is not configured in the system
    """
    cache_key = "default_user_role"
    default_role = cache.get(cache_key)

    if default_role is None:
        try:
            default_role = UserRole.objects.get(role="user")
            cache.set(cache_key, default_role, timeout=3600)  # Cache 1 hour
        except UserRole.DoesNotExist:
            raise RuntimeError(
                "Default 'user' role is not configured. Please create UserRole with role='user'."
            )

    return default_role
