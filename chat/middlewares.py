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
        Called for each incoming WebSocket connection.

        Steps:
        1. Parse the query string for the `token` parameter.
        2. Decode the JWT token and validate it.
        3. Retrieve the corresponding User from the database asynchronously.
        4. Attach the user to `scope["user"]` for downstream consumers.
        5. If token is invalid or user not found, assign AnonymousUser.
        6. Call the downstream ASGI application.

        Args:
            scope (dict): The ASGI connection scope.
            receive (callable): Coroutine to receive ASGI events.
            send (callable): Coroutine to send ASGI events.

        Returns:
            Awaitable: Calls the downstream ASGI application.
        """
        parsed_query_string = parse_qs(scope["query_string"])
        token_values = parsed_query_string.get(b"token")

        if not token_values:
            scope["user"] = AnonymousUser()
            return await self.app(scope, receive, send)

        token = token_values[0].decode("utf-8")

        try:
            access_token = AccessToken(token)
            scope["user"] = await get_user(access_token["user_id"])
        except TokenError:
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)
