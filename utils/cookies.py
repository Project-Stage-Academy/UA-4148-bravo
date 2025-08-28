from django.conf import settings
from core.settings.third_party_settings import SIMPLE_JWT


def set_auth_cookies(response, access_token: str, refresh_token: str = None):
    """
    Set access and refresh tokens as HttpOnly cookies
    using parameters from settings.SIMPLE_JWT.
    """

    cookie_settings = {
        "httponly": SIMPLE_JWT.get("AUTH_COOKIE_HTTP_ONLY", True),
        "secure": SIMPLE_JWT.get("AUTH_COOKIE_SECURE", True),
        "samesite": SIMPLE_JWT.get("AUTH_COOKIE_SAMESITE", "Lax"),
        "path": SIMPLE_JWT.get("AUTH_COOKIE_PATH", "/"),
        "domain": SIMPLE_JWT.get("AUTH_COOKIE_DOMAIN", None),
    }

    access_lifetime = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=int(access_lifetime.total_seconds()),
        **cookie_settings,
    )

    if refresh_token:
        refresh_lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=int(refresh_lifetime.total_seconds()),
            **cookie_settings,
        )

    return response


def clear_auth_cookies(response):
    """
    Remove authentication cookies (access_token and refresh_token).

    Args:
        response: Django/DRF Response object.

    Returns:
        response: The same Response object with cookies deleted.
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response
