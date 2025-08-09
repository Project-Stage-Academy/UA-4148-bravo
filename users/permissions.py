import logging
from functools import wraps
from rest_framework import permissions
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


class IsInvestor(permissions.BasePermission):
    """
    Custom permission to only allow authenticated investors to perform actions.

    This class checks if the requesting user is authenticated and has the 'investor' role.
    """

    def has_permission(self, request, view):
        """
        Checks if the user has the 'investor' role.

        Args:
            request (HttpRequest): The incoming HTTP request.
            view (APIView): The view being accessed.

        Returns:
            bool: True if the user is an authenticated investor, False otherwise.
        """
        user = request.user
        if not user.is_authenticated:
            logger.warning(f"Permission denied: Unauthenticated user attempted to access {view.__class__.__name__}.")
            return False

        user_role = getattr(user, 'role', None)
        if user_role == 'investor':
            logger.debug(f"Permission granted for user {user.id} with role '{user_role}'.")
            return True
        
        logger.warning(
            f"Permission denied for user {user.id}: Role '{user_role}' is not 'investor'."
        )
        return False


class IsStartupUser(permissions.BasePermission):
    """
    Custom permission for startup users to manage their own data.

    This class provides both object-level and global permission checks.
    """

    def has_permission(self, request, view):
        """
        Checks if the user is authenticated and has an associated startup profile.

        Args:
            request (HttpRequest): The incoming HTTP request.
            view (APIView): The view being accessed.

        Returns:
            bool: True if the user is authenticated and linked to a startup, False otherwise.
        """
        user = request.user
        if not user.is_authenticated:
            logger.warning(
                f"Permission denied: Unauthenticated user attempted to access {view.__class__.__name__}."
            )
            return False

        has_startup_profile = hasattr(user, 'startup') and getattr(user, 'startup', None) is not None
        if has_startup_profile:
            logger.debug(f"Permission granted: User {user.id} has a startup profile.")
            return True
        
        logger.warning(
            f"Permission denied: User {user.id} does not have an associated startup profile."
        )
        return False

    def has_object_permission(self, request, view, obj):
        """
        Checks if the user owns the object being accessed.

        Args:
            request (HttpRequest): The incoming HTTP request.
            view (APIView): The view being accessed.
            obj (Model): The object instance being checked.

        Returns:
            bool: True if the user is the owner of the object, False otherwise.
        """
        obj_user = getattr(obj, 'user', None)
        if obj_user and obj_user == request.user:
            logger.debug(
                f"Object-level permission granted for user {request.user.id} on object {obj.pk}."
            )
            return True
        
        logger.warning(
            f"Object-level permission denied for user {request.user.id} on object {obj.pk}."
        )
        return False


def required_permissions(perms):
    """
    Decorator to check if the user has all required permissions.

    If the user lacks any of the specified permissions, a PermissionDenied
    exception is raised and a warning is logged.

    Args:
        perms (list): A list of permission strings in the format
                      '<app_label>.<permission_codename>'.

    Returns:
        function: The decorated view function with permission checks.
    """

    def decorator(view_func):
        """
        Wraps the view function to enforce permission checks.

        Args:
            view_func (function): The original view function to be wrapped.

        Returns:
            function: The wrapped view function with permission enforcement.
        """

        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            """
            Checks the user's permissions before executing the view.

            Args:
                request (HttpRequest): The HTTP request object.
                *args: Positional arguments for the view.
                **kwargs: Keyword arguments for the view.

            Raises:
                PermissionDenied: If the user lacks any of the required permissions.

            Returns:
                HttpResponse: The result of the original view function.
            """
            user_identifier = getattr(request.user, 'username', str(request.user))
            missing_perms = [perm for perm in perms if not request.user.has_perm(perm)]

            if missing_perms:
                logger.warning(
                    f"Permission denied for user '{user_identifier}' — missing permissions: {missing_perms}"
                )
                raise PermissionDenied

            logger.debug(
                f"User '{user_identifier}' has all required permissions: {perms}"
            )
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator