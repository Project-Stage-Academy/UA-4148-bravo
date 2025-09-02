from rest_framework.permissions import BasePermission
from chat.documents import Room
from users.models import User


def check_user_in_room(user: User, room: Room) -> bool:
    """
    Check if a given user is a participant of the specified room.

    Args:
        user (User): Django User instance.
        room (Room): MongoEngine Room instance.

    Returns:
        bool: True if the user is authenticated and their email is in the room's participants list,
              otherwise False.
    """
    if not user or not user.is_authenticated:
        return False
    if not room or not getattr(room, "participants", None):
        return False
    return user.email in room.participants


class IsOwnerOrRecipient(BasePermission):
    """
    Custom DRF permission to ensure that only the sender, recipient,
    and participants of a room can access a message object.
    """

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission check.

        Args:
            request: The current HTTP request.
            view: The DRF view where the permission is applied.
            obj: The object being accessed (expected to be a Message instance).

        Returns:
            bool: True if the requesting user is either the sender or the recipient
                  of the message, and is a participant of the corresponding room.
        """
        if not check_user_in_room(request.user, getattr(obj, "room", None)):
            return False

        return (
                obj.sender_email == request.user.email
                or obj.receiver_email == request.user.email
        )
