import logging
import os
from django.core.cache import cache
import time
import sentry_sdk

logger = logging.getLogger(__name__)

MESSAGE_RATE_LIMIT = int(os.getenv("MESSAGE_RATE_LIMIT", 5))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 10))


def is_rate_limited(user_id: int, room_name: str = "UNKNOWN") -> bool:
    """
    Returns True if the user exceeded the allowed message rate.

    Args:
        user_id (int): ID of the user.
        room_name (str): Optional room name for logging.

    Returns:
        bool: True if rate limit exceeded, False otherwise.
    """
    key = f"msg_rate_{user_id}"
    timestamps = cache.get(key, [])
    now = time.time()

    timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]

    if len(timestamps) >= MESSAGE_RATE_LIMIT:
        logger.warning("[RATE_LIMIT] User %s exceeded limit in room %s", user_id, room_name)
        sentry_sdk.capture_message(f"Rate limit exceeded by user {user_id} in room {room_name}",
                                   level="warning")
        return True

    timestamps.append(now)
    cache.set(key, timestamps, timeout=RATE_LIMIT_WINDOW)
    return False
