import logging
from rest_framework import permissions
from django.core.exceptions import PermissionDenied
from startups.models import Startup

logger = logging.getLogger(__name__)


class IsInvestor(permissions.BasePermission):
    """
    Allows access only to authenticated users with the 'investor' role.
    """
    def has_permission(self, request, view):
        user = request.user

        if not getattr(user, 'is_authenticated', False):
            logger.warning(f"Permission denied: Unauthenticated user tried to access {view.__class__.__name__}.")
            return False

        user_role = getattr(user, 'role', None)
        
        if hasattr(user.__class__, 'Roles') and hasattr(user.__class__.Roles, 'INVESTOR'):
            valid_role = user_role == user.__class__.Roles.INVESTOR
        else:
            valid_role = user_role == 'investor'

        if valid_role:
            logger.debug(f"Permission granted for user {user.id} with role '{user_role}'.")
            return True

        logger.warning(f"Permission denied for user {user.id}: Role '{user_role}' is not 'investor'.")
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

        startup_id = getattr(user, 'startup_id', None)
        if startup_id and Startup.objects.filter(id=startup_id).exists():
            logger.debug(f"Permission granted: User {user.id} linked to startup {startup_id}.")
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