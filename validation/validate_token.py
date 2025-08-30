import jwt
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings


def safe_decode(token: str):
    """
    Safely decode a JWT and verify its signature and expiration.
    Raises InvalidToken or TokenExpired if the token is invalid or expired.
    """
    if not token or len(token.split(".")) != 3:
        raise InvalidToken("Token is malformed.")

    try:
        payload = jwt.decode(
            token,
            key=settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_exp": True}
        )
    except jwt.ExpiredSignatureError:
        raise TokenError("Token has expired.")
    except Exception as e:
        raise InvalidToken(f"Could not decode token: {str(e)}")

    return payload
