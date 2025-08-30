from functools import wraps
import logging
import sentry_sdk

logger = logging.getLogger(__name__)


def log_and_capture(entity_name: str, exception_cls=Exception):
    """
    Universal decorator for logging and Sentry integration.
    Can wrap DRF serializer methods or MongoEngine save methods.

    Args:
        entity_name (str): Type of entity ('room', 'message', etc.)
        exception_cls (Exception): Type of exception to catch (default: all)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                result = func(self, *args, **kwargs)
                # Determine identifier and extra info
                if hasattr(result, 'name'):
                    identifier = result.name
                    extra = getattr(result, 'participants', '')
                elif hasattr(result, 'sender_email'):
                    identifier = getattr(result, 'sender_email', 'UNKNOWN')
                    extra = f"{getattr(result, 'receiver_email', '')} | room={getattr(result.room, 'name', 'UNKNOWN')}"
                else:
                    identifier = 'UNKNOWN'
                    extra = ''
                logger.info("[%s_SAVE] Success | %s | %s", entity_name.upper(), identifier, extra)
                return result
            except exception_cls as e:
                logger.error("[%s_SAVE] Failed | error=%s", entity_name.upper(), e)
                sentry_sdk.capture_exception(e)
                raise

        return wrapper

    return decorator
