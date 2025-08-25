import logging
from rest_framework import permissions
from startups.models import Startup

logger = logging.getLogger(__name__)


class IsInvestor(permissions.BasePermission):
    """
    Allows access only to authenticated users who are registered as investors.
    """

    def has_permission(self, request, view):
        user = request.user

        if not getattr(user, 'is_authenticated', False):
            logger.warning(f"Permission denied: Unauthenticated user tried to access {view.__class__.__name__}.")
            return False

        if hasattr(user, 'investor'):
            logger.debug(f"Permission granted for user {user.id} as investor.")
            return True

        logger.warning(f"Permission denied for user {user.id}: Not an investor.")
        return False


class IsStartupUser(permissions.BasePermission):
    """
    Allows access only to authenticated users linked to a startup.
    """

    def has_permission(self, request, view):
        user = request.user

        if not getattr(user, 'is_authenticated', False):
            logger.warning(f"Permission denied: Unauthenticated user tried to access {view.__class__.__name__}.")
            return False

        if hasattr(user, 'startup'):
            logger.debug(f"Permission granted: User {user.id} linked to startup {getattr(user.startup, 'id', None)}.")
            return True

        if Startup.objects.filter(user_id=getattr(user, 'id', None)).exists():
            logger.debug(f"Permission granted: User {user.id} linked to a startup via DB check.")
            return True

        logger.warning(f"Permission denied: User {user.id} has no valid startup linked.")
        return False

    def has_object_permission(self, request, view, obj):
        obj_user = getattr(obj, 'user', None)
        if obj_user == request.user:
            logger.debug(f"Object-level permission granted for user {request.user.id} on object {obj.pk}.")
            return True

        logger.warning(f"Object-level permission denied for user {request.user.id} on object {obj.pk}.")
        return False
