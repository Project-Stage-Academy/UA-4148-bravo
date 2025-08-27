from rest_framework import permissions


class IsSavedStartupOwner(permissions.BasePermission):
    """
    Custom permission to allow only the owner of a SavedStartup (its investor) to modify or delete it.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the request user's investor profile matches the
        investor linked to the SavedStartup object.
        """

        investor_profile = getattr(request.user, 'investor', None)
        if not investor_profile:
            return False
        return obj.investor == investor_profile
