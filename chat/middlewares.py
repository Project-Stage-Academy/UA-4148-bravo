from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken, TokenError
from users.models import User


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
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class WebSocketJWTAuthMiddleware:
    """
    Custom ASGI middleware for authenticating WebSocket connections using JWT.

    This middleware extracts a JWT access token from the query string,
    verifies it using Django REST Framework SimpleJWT, and attaches
    the corresponding User object to the ASGI `scope`. If the token
    is invalid or missing, the user is set as AnonymousUser.

    Attributes:
        app (ASGI app): The downstream ASGI application to call.
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

        This method authenticates a WebSocket connection using a JWT access token
        passed in the query string. If the token is valid, the corresponding user
        is attached to `scope["user"]` for downstream consumers. If the token is
        missing or invalid, the WebSocket connection is immediately closed with
        code 1008 (policy violation).

        Steps:
        1. Parse the query string for the `token` parameter.
        2. Decode and validate the JWT token.
        3. Retrieve the associated user asynchronously from the database.
        4. Attach the user to `scope["user"]` for downstream consumers.
        5. Close the WebSocket if the token is missing or invalid.
        6. Forward the connection to the downstream ASGI application if authenticated.

        Args:
            scope (dict): ASGI connection scope.
            receive (Callable): Coroutine to receive ASGI events.
            send (Callable): Coroutine to send ASGI events.

        Returns:
            Awaitable: Invokes the downstream ASGI application if the token is valid,
            otherwise closes the WebSocket connection with code 1008.
        """
        parsed_query_string = parse_qs(scope["query_string"].decode("utf-8"))
        token_values = parsed_query_string.get("token")

        if not token_values:
            await send({'type': 'websocket.close', 'code': 1008})
            return

        token = token_values[0]

        try:
            access_token = AccessToken(token)
            scope["user"] = await get_user(access_token["user_id"])
        except TokenError:
            await send({'type': 'websocket.close', 'code': 1008})
            return

        await self.app(scope, receive, send)
