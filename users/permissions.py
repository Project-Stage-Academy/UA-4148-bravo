import logging
from functools import wraps
from rest_framework import permissions
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)

class IsInvestor(permissions.BasePermission):
    """
    Custom permission to only allow investors to create subscriptions.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'investor'


class IsStartupUser(permissions.BasePermission):
    """
    Custom permission to only allow startup users to edit their own profile.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'startup')

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

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


logger.debug("This is a debug message.")
logger.info("Informational message.")
logger.warning("Warning occurred!")
logger.error("An error happened.")
logger.critical("Critical issue!")
