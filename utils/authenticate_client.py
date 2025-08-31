from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient

from users.models import User


def authenticate_client(client: APIClient, user: User) -> None:
    """
    Authenticate a Django REST Framework test client using a JWT access token.

    This function generates a JWT access token for the given user and sets it
    as a cookie on the provided APIClient instance. It also forcibly authenticates
    the client with the given user.

    Args:
        client (APIClient): The DRF test client instance to authenticate.
        user (User): The Django user instance to authenticate as.

    Side Effects:
        - Sets the "access_token" cookie on the client.
        - Calls client.force_authenticate(user=user) to attach the user to the client.
    """
    token = RefreshToken.for_user(user).access_token
    client.cookies["access_token"] = str(token)
    client.force_authenticate(user=user)
