import jwt
from rest_framework_simplejwt.exceptions import InvalidToken


def safe_decode(token: str):
    """
    Safely decode a JWT without verifying its signature.
    Ensures the token has a valid structure before decoding.
    """
    if not token or len(token.split(".")) != 3:
        raise InvalidToken("Token is malformed.")
    return jwt.decode(token, options={"verify_signature": False})
