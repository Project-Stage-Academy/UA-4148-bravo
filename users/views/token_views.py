import logging
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from users.serializers.token_serializer import CustomTokenObtainPairSerializer
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect

logger = logging.getLogger(__name__)


class CSRFTokenView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        token = get_token(request)
        return Response({"csrfToken": token})

@extend_schema(
    tags=["Auth"],
    summary="Obtain JWT access/refresh tokens",
    request=CustomTokenObtainPairSerializer,
    responses={
        200: CustomTokenObtainPairSerializer,
        401: OpenApiResponse(description="Invalid credentials"),
    },
)
@method_decorator(csrf_protect, name="post")
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom view for obtaining JWT tokens.
    Uses CustomTokenObtainPairSerializer for token generation.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to obtain JWT tokens.

        Steps performed:
        1. Validate user credentials using CustomTokenObtainPairSerializer.
        2. Generate a refresh token and access token for the authenticated user.
        3. Return the access token in the response body.
        4. Set the refresh token as an HTTPOnly cookie.

        Args:
            request: DRF Request object containing user credentials.

        Returns:
            Response: DRF Response containing the access token and
                      the refresh token set in an HTTPOnly cookie.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        response = Response({"access": str(access)}, status=status.HTTP_200_OK)

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=60 * 60 * 24,
        )
        return response


@extend_schema(
    tags=["Auth"],
    summary="Refresh JWT access token",
)
@method_decorator(csrf_protect, name="post")
class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom view to refresh JWT access tokens using a refresh token stored in an HTTPOnly cookie.

    This view overrides the default TokenRefreshView to:
    1. Read the refresh token from the 'refresh_token' cookie instead of the request body.
    2. Return a new access token (and optionally a new refresh token) in the response body.

    Using cookies for refresh tokens improves security by preventing JavaScript
    from accessing them directly (mitigating XSS risks).
    """

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to refresh JWT access tokens.

        Steps performed:
        1. Retrieve the refresh token from the 'refresh_token' HTTPOnly cookie.
        2. Validate the refresh token using the standard SimpleJWT serializer.
        3. Return a new access token (and optionally a new refresh token) in the response.

        Args:
            request: DRF Request object. The refresh token is expected to be in cookies.

        Returns:
            Response: DRF Response containing the new access token (and refresh token if rotation is enabled).
                      Returns 401 if no refresh token cookie is found.
        """
        refresh = request.COOKIES.get("refresh_token")
        if refresh is None:
            return Response({"detail": "No refresh token provided"}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(data={"refresh": refresh})
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Auth"],
    summary="Logout (blacklist refresh token)",
)
@method_decorator(csrf_protect, name="post")
class JWTLogoutView(APIView):
    """
    Custom view to handle user logout and invalidate JWT refresh tokens stored in cookies.

    This view performs the following actions:
    1. Reads the refresh token from the 'refresh_token' HTTPOnly cookie.
    2. Attempts to blacklist the refresh token to prevent further use (requires SimpleJWT blacklist app enabled).
    3. Deletes the 'refresh_token' cookie from the client to complete logout.
    """

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for logging out the user.

        Steps performed:
        1. Retrieve the refresh token from the 'refresh_token' cookie.
        2. If present, attempt to blacklist the token to revoke it.
        3. Return a success response and remove the cookie from the client.

        Args:
            request: DRF Request object. Expects the refresh token in cookies.

        Returns:
            Response: DRF Response confirming successful logout.
        """
        refresh = request.COOKIES.get("refresh_token")
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except Exception:
                pass

        response = Response({"detail": "Successfully logged out"}, status=status.HTTP_200_OK)
        response.delete_cookie("refresh_token")
        return response
