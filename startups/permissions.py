from rest_framework import permissions

class IsStartupOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow read-only access for safe methods.
    For write actions:
    - only the owner of the startup,
    - or admin (is_staff).
    """

    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS = GET, HEAD, OPTIONS
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if getattr(request.user, "is_staff", False):
            return True

        return getattr(obj, "user_id", None) == getattr(request.user, "id", None)

