import logging
from rest_framework import permissions
from startups.models import Startup
from investors.models import Investor
from rest_framework.permissions import BasePermission
from rest_framework import exceptions

logger = logging.getLogger(__name__)


class IsInvestor(permissions.BasePermission):
    """
    Allows access only to authenticated users who are registered as investors.
    """

    def has_permission(self, request, view):
        """
        Checks if the request.user is authenticated and linked to an Investor profile.
        Logs a warning if the user is not an investor.
        """
        if not request.user or not request.user.is_authenticated:
            return False

        is_investor = Investor.objects.filter(user=request.user).exists()

        if is_investor:
            logger.debug(
                "Permission granted for user %s as investor for view %s.",
                request.user.pk,
                view.__class__.__name__
            )
            return True
        else:
            logger.warning(
                "Permission denied for user %s: Not an investor for view %s.",
                request.user.pk,
                view.__class__.__name__,
                extra={"user_id": request.user.pk, "view": view.__class__.__name__}
            )
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

        try:
            startup = getattr(user, 'startup', None)
            _ = startup.id
        except Startup.DoesNotExist:
            startup = None
        except Exception:
            startup = None
        if startup is not None:
            logger.debug(f"Permission granted: User {user.id} linked to startup {getattr(startup, 'id', None)}.")
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


class CanCreateCompanyPermission(permissions.BasePermission):
    """
    Permission to check if a user can create a new Startup or Investor profile.
    Denies permission if the user already owns a Startup or an Investor profile.
    """
    message = "You have already created a company profile (Startup or Investor) and cannot create another."

    def has_permission(self, request, view):
        """
        Check if the user is authenticated and does not already have a company.
        """
        if not request.user or not request.user.is_authenticated:
            return False

        has_startup = Startup.objects.filter(user=request.user).exists()
        has_investor = Investor.objects.filter(user=request.user).exists()

        if has_startup or has_investor:
            return False

        return True


class IsAuthenticatedOr401(BasePermission):
    """
    Like IsAuthenticated, but returns 401 instead of 403 when the user is not authenticated.
    """

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        raise exceptions.NotAuthenticated("Authentication credentials were not provided.")

    def authenticate_header(self, request):
        return 'Bearer'


class IsAuthenticatedInvestor403(BasePermission):
    """
    Permission that enforces:
      - User must be authenticated.
      - An Investor record must exist for this user.
    Any failure → 403 Forbidden (per acceptance criteria).
    """

    message = "Only authenticated investors are allowed to perform this action."

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            logger.warning(
                "Permission denied: unauthenticated user tried to access %s.",
                view.__class__.__name__,
            )
            return False

        is_investor = hasattr(user, "investor") or Investor.objects.filter(user=user).exists()

        if not is_investor:
            logger.warning(
                "Permission denied: user %s is not an investor for %s.",
                user.id,
                view.__class__.__name__,
            )
            return False

        logger.debug(
            "Permission granted: user %s is an investor for %s.",
            user.id,
            view.__class__.__name__,
        )
        return True


class HasActiveCompanyAccount(BasePermission):
    """
    Custom permission to ensure:
    - User account is active
    - User is linked to a Startup OR Investor entity
    """

    message = "You must have an active account and be linked to a company (Startup or Investor)."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        return user.is_active and (
                hasattr(user, "startup") or hasattr(user, "investor")
        )
