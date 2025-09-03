from rest_framework.views import APIView
from chat.permissions import IsOwnerOrRecipient
from users.cookie_jwt import CookieJWTAuthentication
from users.permissions import IsAuthenticatedOr401


class ChatCookieJWTProtectedView(APIView):
    """
    Base view that enforces authentication via access_token cookie
    and ensures the user is authenticated.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticatedOr401, IsOwnerOrRecipient]
