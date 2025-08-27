import logging
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    inline_serializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from users.serializers.token_serializer import CustomTokenObtainPairSerializer
from rest_framework import status, serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from validation.validate_token import safe_decode

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Auth"],
    summary="Get CSRF token",
    description=(
            "Returns a CSRF token in JSON and sets the CSRF cookie. "
            "Call this before any POST/PUT/PATCH/DELETE requests."
    ),
    responses={
        200: OpenApiResponse(
            description="CSRF token retrieved successfully",
            response=inline_serializer(
                name="CsrfTokenResponse",
                fields={"csrfToken": serializers.CharField()},
            ),
        )
    },
)
class CSRFTokenView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        """
        Returns a CSRF token in JSON and sets the `csrftoken` cookie.
        """
        token = get_token(request)
        return Response({"csrfToken": token})


@extend_schema(
    tags=["Auth"],
    summary="Obtain JWT (sets cookies)",
    description="Authenticates user, stores access/refresh tokens in HttpOnly cookies (access ~15m, refresh ~7d), returns minimal user info only.",
    request=CustomTokenObtainPairSerializer,
    responses={
        200: OpenApiResponse(
            description="Authenticated successfully",
            response=inline_serializer(
                name="LoginResponse",
                fields={"email": serializers.EmailField(), "user_id": serializers.IntegerField()},
            ),
        ),
        400: OpenApiResponse(
            description="Tokens missing or bad request",
            response=inline_serializer(name="LoginErrorResponse", fields={"detail": serializers.CharField()}),
        ),
        401: OpenApiResponse(description="Invalid credentials"),
    },
)
@method_decorator(csrf_protect, name="post")
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Issues access & refresh tokens (in HttpOnly cookies) upon successful authentication.
    Response body contains minimal user info only (no tokens in body).
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        Steps:
        1) Validate credentials via serializer (SimpleJWT).
        2) On success, set `refresh_token` & `access_token` cookies.
        3) Return user info in JSON (no tokens in body).
        """
        response = super().post(request, *args, **kwargs)

        if "refresh" not in response.data or "access" not in response.data:
            return Response({"detail": "Tokens missing."}, status=status.HTTP_400_BAD_REQUEST)

        response.set_cookie(
            key="refresh_token",
            value=response.data["refresh"],
            httponly=True,
            secure=True,
            samesite=None,
            max_age=60 * 60 * 24 * 7,
        )

        response.set_cookie(
            key="access_token",
            value=response.data["access"],
            httponly=True,
            secure=True,
            samesite=None,
            max_age=60 * 15,
        )

        user = request.user
        response.data = {"email": getattr(user, "email", None), "user_id": getattr(user, "id", None)}

        return response


@extend_schema(
    tags=["Auth"],
    summary="Refresh JWT access token (cookie-based)",
    description="Reads refresh_token from HttpOnly cookie, validates it, issues new access token in cookie. Does not return tokens in body.",
    responses={
        200: OpenApiResponse(
            description="Access token refreshed",
            response=inline_serializer(name="RefreshResponse", fields={"detail": serializers.CharField()}),
        ),
        404: OpenApiResponse(
            description="Refresh token missing",
            response=inline_serializer(name="RefreshMissingResponse", fields={"detail": serializers.CharField()}),
        ),
        205: OpenApiResponse(
            description="Refresh token invalid/expired; cookies cleared",
            response=inline_serializer(name="RefreshClearedResponse", fields={"detail": serializers.CharField()}),
        ),
        400: OpenApiResponse(
            description="Access token not generated",
            response=inline_serializer(name="RefreshBadResponse", fields={"detail": serializers.CharField()}),
        ),
    },
)
@method_decorator(csrf_protect, name="post")
class CookieTokenRefreshView(TokenRefreshView):
    """
    Refreshes the access token using the refresh token from HttpOnly cookie.
    Sets new access token in cookie. Does not return tokens in response body.
    """

    def post(self, request, *args, **kwargs):
        """
        Steps:
        1) Read `refresh_token` from cookies.
        2) Validate/parse it. On error — clear cookies and return 205.
        3) Issue new access token and set it in `access_token` cookie.
        4) Return { "detail": "Access token refreshed" }.
        """
        refresh = request.COOKIES.get("refresh_token")
        if not refresh:
            return Response({"detail": "Refresh token missing."}, status=status.HTTP_404_NOT_FOUND)

        try:
            safe_decode(refresh)
        except Exception as e:
            response = Response({"detail": str(e)}, status=status.HTTP_205_RESET_CONTENT)
            response.delete_cookie("refresh_token")
            response.delete_cookie("access_token")
            return response

        serializer = self.get_serializer(data={"refresh": refresh})
        serializer.is_valid(raise_exception=True)

        access = serializer.validated_data.get("access")
        if not access:
            return Response({"detail": "Access token not generated."}, status=status.HTTP_400_BAD_REQUEST)

        response = Response({"detail": "Access token refreshed"}, status=status.HTTP_200_OK)
        response.set_cookie(
            key="access_token",
            value=access,
            httponly=True,
            secure=True,
            samesite=None,
            max_age=60 * 15,
        )
        return response


@extend_schema(
    tags=["Auth"],
    summary="Logout (blacklist refresh token)",
    description=(
            "Attempts to blacklist the refresh token (if blacklist app enabled) "
            "and deletes both `refresh_token` and `access_token` cookies."
    ),
    responses={
        205: OpenApiResponse(
            description="Logout successful",
            response=inline_serializer(
                name="LogoutResponse",
                fields={"detail": serializers.CharField()},
            ),
        ),
    },
)
@method_decorator(csrf_protect, name="post")
class JWTLogoutView(APIView):
    """
    Logs out the user by invalidating the refresh token (best-effort) and clearing cookies.
    Requires authentication (access token).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Steps:
        1) Read `refresh_token` from cookies.
        2) Try to blacklist it (if supported).
        3) Clear both cookies and return 205.
        """
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()  # requires simplejwt blacklist app
            except Exception as e:
                logger.warning(f"Failed to blacklist refresh token: {str(e)}")

        response = Response({"detail": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        response.delete_cookie("refresh_token")
        response.delete_cookie("access_token")
        return response
