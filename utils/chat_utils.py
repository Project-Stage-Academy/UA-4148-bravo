import re
from typing import Tuple
from chat.documents import Room
from users.models import User
from mongoengine.errors import ValidationError
import logging

logger = logging.getLogger(__name__)


def sanitize_email_for_room(email: str) -> str:
    """
    Sanitize an email to be safe for use in a Room.name.
    All characters except a-z, A-Z, 0-9, '_' and '-' are replaced with '_'.

    Args:
        email (str): The email address to sanitize.

    Returns:
        str: Sanitized string safe for Room.name.
    """
    return re.sub(r'[^a-zA-Z0-9_-]', '_', email)


def get_or_create_room(investor: User, startup: User) -> Tuple[Room, bool]:
    """
    Create a new chat room or retrieve an existing one between
    an investor and a startup. Automatically generates a valid
    room name based on sanitized emails.

    Args:
        investor (User): Investor user instance.
        startup (User): Startup user instance.

    Returns:
        Tuple[Room, bool]: The Room instance and a boolean indicating
                           whether it was created (True) or retrieved (False).
    """
    inv_clean = sanitize_email_for_room(investor.email)
    st_clean = sanitize_email_for_room(startup.email)
    room_name = f"{inv_clean}_{st_clean}"

    try:
        room = Room.objects.get(name=room_name)
        return room, False
    except Room.DoesNotExist:
        room = Room(name=room_name, participants=[investor.email, startup.email])
        try:
            room.save()
            return room, True
        except ValidationError as ve:
            logger.error("[ROOM_SAVE] Failed | error=%s", ve)
            raise ve
