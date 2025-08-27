from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from users.cookie_jwt import CookieJWTAuthentication


class CookieJWTProtectedView(APIView):
    """
    Base view that enforces authentication via access_token cookie
    and ensures the user is authenticated.
    """

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
