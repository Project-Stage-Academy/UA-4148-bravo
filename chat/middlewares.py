import logging
from http.cookies import SimpleCookie
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from users.models import User
from users.tokens import safe_decode

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user(user_id):
    """
    Retrieve a User instance by ID from the database asynchronously.

    Args:
        user_id (int): The ID of the user to fetch.

    Returns:
        User | AnonymousUser: Returns the User object if found,
                              otherwise returns an AnonymousUser.
    """
    try:
        return User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        return AnonymousUser()


class WebSocketJWTAuthMiddleware:
    """
    ASGI middleware for authenticating WebSocket connections using JWT
    stored in an HttpOnly cookie.

    The middleware parses the 'access_token' cookie, validates the JWT using
    safe_decode, and sets scope["user"] to the authenticated user. If the
    token is missing or invalid, the WebSocket connection is closed with code 1008.
    """

    def __init__(self, app):
        """
        Initialize the middleware with the downstream ASGI app.

        Args:
            app: The ASGI application to wrap.
        """
        self.app = app

    async def __call__(self, scope, receive, send):
        """
        ASGI middleware entry point for WebSocket connections.

        Authenticates the WebSocket connection using a JWT access token stored
        in an HttpOnly cookie. If valid, attaches the authenticated user to
        `scope["user"]`. If the token is missing or invalid, closes the connection
        with code 1008 (policy violation).

        Args:
            scope (dict): ASGI connection scope containing headers and other metadata.
            receive (Callable): Coroutine to receive ASGI events.
            send (Callable): Coroutine to send ASGI events.

        Returns:
            Awaitable: Forwards the connection to the downstream ASGI app if
            authentication succeeds, otherwise closes the connection.
        """
        cookie_header = dict(scope["headers"]).get(b"cookie", b"").decode()
        cookies = SimpleCookie()
        cookies.load(cookie_header)

        token_cookie = cookies.get("access_token")
        if not token_cookie:
            logger.warning("WS connection rejected: no access_token cookie")
            await send({'type': 'websocket.close', 'code': 1008})
            return
        token = token_cookie.value

        try:
            payload = safe_decode(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise ValueError("Token payload missing user_id")
            scope["user"] = await get_user(user_id)
        except Exception as e:
            logger.warning(f"WS connection rejected: invalid token. Error: {e}")
            await send({'type': 'websocket.close', 'code': 1008})
            return

        await self.app(scope, receive, send)
