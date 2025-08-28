from rest_framework.views import APIView
from users.cookie_jwt import CookieJWTAuthentication
from rest_framework.permissions import IsAuthenticated


class CookieJWTProtectedView(APIView):
    """
    Base view that enforces authentication via access_token cookie
    and ensures the user is authenticated.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
