from rest_framework import permissions


class IsSavedStartupOwner(permissions.BasePermission):
    """
    Custom permission to allow only the owner of a SavedStartup (its investor) to modify or delete it.
    """

    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, "investor"):
            return False
        return obj.investor_id == request.user.investor.pk
