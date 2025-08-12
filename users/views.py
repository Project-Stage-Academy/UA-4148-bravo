import logging
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
import requests
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserRole

logger = logging.getLogger(__name__)  # Added this

# Custom view to use the custom JWT serializer
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Optional logging setup (can be removed if not needed)
if __name__ == "__main__":
    logger.debug("This is a debug message.")
    logger.info("Informational message.")
    logger.warning("Warning occurred!")
    logger.error("An error happened.")
    logger.critical("Critical issue!")



User = get_user_model()
role = UserRole.objects.get(role="user")

class OAuthTokenObtainPairView(TokenObtainPairView):
    """
    Extended token authentication endpoint that supports both traditional email/password
    and OAuth provider authentication (Google/GitHub).
    
    Inherits from Djoser's TokenObtainPairView to maintain all standard functionality
    while adding OAuth support through a unified authentication endpoint.
    
    Endpoint: users/oauth/login/
    Methods: POST
    
    Request Formats:
        - OAuth: {"provider": "google|github", "access_token": "oauth_token"}
        - Password: {"email": "user@example.com", "password": "password123"}
    """
    
    def post(self, request, *args, **kwargs):
        """
        Handle authentication requests, routing to appropriate method based on input.
        
        Args:
            request: DRF request object containing authentication credentials
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
            
        Returns:
            Response: JSON containing either:
                - JWT tokens and user data (success)
                - Error message (failure)
                
        Status Codes:
            - 200 OK: Successful authentication
            - 400 Bad Request: Missing/invalid parameters
            - 401 Unauthorized: Invalid credentials
        """
        # Check if this is an OAuth request
        provider = request.data.get('provider')  # 'google' or 'github'
        access_token = request.data.get('access_token')
        
        if provider and access_token:
            return self.handle_oauth(provider, access_token)
        
        # Fall back to standard email/password auth
        return super().post(request, *args, **kwargs)
    
    def handle_oauth(self, provider, access_token):
        """
        Route OAuth authentication requests to the appropriate provider handler.
        
        Args:
            provider: String identifying the OAuth provider ('google' or 'github')
            access_token: Valid OAuth access token from the provider
            
        Returns:
            Response: JSON response from the provider handler or error if unsupported
            
        Raises:
            HTTP 400: If provider is not supported
        """
        if provider == 'google':
            return self.handle_google_oauth(access_token)
        elif provider == 'github':
            return self.handle_github_oauth(access_token)
        else:
            return Response(
                {"error": "Unsupported OAuth provider"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def handle_google_oauth(self, access_token):
        """
        Authenticate using Google OAuth access token.
        
        1. Validates token with Google's API
        2. Retrieves user profile information
        3. Creates/updates local user record
        4. Issues JWT tokens
        
        Args:
            access_token: Valid Google OAuth access token
            
        Returns:
            Response: JSON containing JWT tokens and user data or error message
            
        Status Codes:
            - 200 OK: Successful authentication
            - 400 Bad Request: Invalid token or missing email
        """
        google_userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(google_userinfo_url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException:
            return Response(
                {"error": "Invalid Google token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = data.get("email")
        if not email:
            return Response(
                {"error": "Email not provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        first_name = data.get("given_name", "")
        last_name = data.get("family_name", "")

        user, _ = self.get_or_create_user(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "password": None,
                "user_phone": "",
                "title": "",
                "role": role
            }
        )

        return self.generate_jwt_response(user)
    
    def handle_github_oauth(self, access_token):
        """
        Authenticate using GitHub OAuth access token.
        
        1. Validates token with GitHub's API
        2. Retrieves user profile and primary email
        3. Creates/updates local user record
        4. Issues JWT tokens
        
        Args:
            access_token: Valid GitHub OAuth access token
            
        Returns:
            Response: JSON containing JWT tokens and user data or error message
            
        Status Codes:
            - 200 OK: Successful authentication
            - 400 Bad Request: Invalid token or missing email
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        try:
            # Get user info
            user_response = requests.get(
                "https://api.github.com/user", 
                headers=headers
            )
            user_response.raise_for_status()
            user_data = user_response.json()
            
            # Get email (might need separate request)
            email = user_data.get("email")
            if not email:
                email_response = requests.get(
                    "https://api.github.com/user/emails", 
                    headers=headers
                )
                email_response.raise_for_status()
                emails = email_response.json()
                primary_email = next(
                    (e for e in emails if e.get("primary")), 
                    None
                )
                if primary_email:
                    email = primary_email.get("email")

            if not email:
                return Response(
                    {"error": "Email not provided by GitHub"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Process name
            username = user_data.get("login")
            name_parts = user_data.get("name", "").split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            user, _ = self.get_or_create_user(
                email=email,
                defaults={
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "password": None,
                    "user_phone": "",
                    "title": "",
                    "role": role
                }
            )

            return self.generate_jwt_response(user)
            
        except requests.RequestException:
            return Response(
                {"error": "Invalid GitHub token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def get_or_create_user(self, email, defaults):
        """
        Helper method to get or create user with intelligent field updates.
        
        Args:
            email: User's email address (primary lookup key)
            defaults: Dictionary of default values for new user creation
            
        Returns:
            tuple: (user_object, created_bool) where:
                - user_object: The retrieved or created user instance
                - created_bool: Boolean indicating if user was created
        """
        user, created = User.objects.get_or_create(
            email=email,
            defaults=defaults
        )
        
        if created:
            user.set_unusable_password()
            user.save()
        else:
            update_fields = {}
            if not user.first_name and defaults.get('first_name'):
                update_fields['first_name'] = defaults['first_name']
            if not user.last_name and defaults.get('last_name'):
                update_fields['last_name'] = defaults['last_name']
            
            if update_fields:
                User.objects.filter(pk=user.pk).update(**update_fields)
                user.refresh_from_db()
        
        return user, created
    
    def generate_jwt_response(self, user):
        """
        Generate standardized JWT token response with user data.
        
        Args:
            user: Authenticated user instance
            
        Returns:
            Response: DRF Response object containing:
                - refresh: JWT refresh token
                - access: JWT access token
                - user: Serialized user data
        """
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.user_id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "user_phone": user.user_phone,
                "title": user.title,
                "role": str(user.role) if user.role else None
            }
        })