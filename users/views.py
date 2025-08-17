# Python standard library
import logging
import secrets
from datetime import timedelta
from smtplib import SMTPException

# Django imports
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
    ImproperlyConfigured,
)
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import reverse
from django.template.loader import render_to_string
from django.utils import timezone

# Third-party imports
import requests
from djoser.email import PasswordResetEmail
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

# Local application imports
from .constants import (
    ACTIVATION_EMAIL_TEMPLATE,
    SUPPORT_TEXT,
    EMAIL_VERIFICATION_TOKEN,
)
from .models import User, UserRole
from .serializers import (
    CustomTokenObtainPairSerializer,
    CustomUserCreateSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    ResendEmailSerializer,
    UserSerializer,
)

logger = logging.getLogger(__name__)


class RegisterThrottle(AnonRateThrottle):
    """Rate limiting for registration endpoint."""
    rate = '5/hour'


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom view for obtaining JWT tokens."""
    serializer_class = CustomTokenObtainPairSerializer


class UserRegistrationView(APIView):
    """Handle user registration with email verification."""
    permission_classes = [AllowAny]
    serializer_class = CustomUserCreateSerializer
    throttle_classes = [RegisterThrottle]

    def _generate_verification_token(self):
        return secrets.token_urlsafe(32)

    def _send_verification_email(self, request, user, token):
        verification_relative_url = reverse('verify-email', kwargs={'user_id': user.user_id, 'token': token})
        verification_url = f"{request.scheme}://{request.get_host()}{verification_relative_url}"

        context = {'user': user, 'verification_url': verification_url}
        subject = 'Verify Your Email'
        html_message = render_to_string('email/activation.html', context)
        plain_message = f"Please verify your email by visiting: {verification_url}"

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response({'status': 'error', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            token = self._generate_verification_token()
            user.email_verification_token = token
            user.email_verification_sent_at = timezone.now()
            user.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
            self._send_verification_email(request, user, token)
            return Response({
                'status': 'success',
                'message': 'Registration successful! Please check your email to verify your account.',
                'user_id': user.user_id,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error during registration: {str(e)}", exc_info=True)
            return Response({'status': 'error', 'message': 'Registration failed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyEmailView(APIView):
    """Handle email verification."""
    permission_classes = [AllowAny]

    def get(self, request, user_id, token):
        try:
            # Try to fetch by user_id+token first
            try:
                user = User.objects.get(
                    user_id=user_id,
                    email_verification_token=token
                )
            except User.DoesNotExist:
                # If user exists and already active, return idempotent success
                try:
                    existing_user = User.objects.get(user_id=user_id)
                    if existing_user.is_active:
                        return Response(
                            {'status': 'success', 'message': 'Email is already verified.'},
                            status=status.HTTP_200_OK
                        )
                except User.DoesNotExist:
                    pass
                return Response(
                    {'status': 'error', 'message': 'Invalid verification link.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check token expiry (24 hours)
            token_expired = (
                user.email_verification_sent_at is None or
                (timezone.now() - user.email_verification_sent_at) > timedelta(hours=24)
            )
            if token_expired:
                logger.warning(f"Expired verification token for user {user.email}")
                return Response(
                    {'status': 'error', 'message': 'Verification link has expired.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Reviewer fix: prefer duck typing over hasattr()
            try:
                user.confirm_pending_email()
            except AttributeError:
                # If the model doesn't implement confirm_pending_email, ignore silently.
                pass
            except DjangoValidationError as e:
                if getattr(e, "code", None) == "no_pending_email":
                    logger.info(f"No pending email to confirm for {user.email}")
                else:
                    logger.warning(f"Failed to confirm pending email for {user.email}: {e}")
                    return Response(
                        {"status": "error", "message": str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            user.is_active = True
            user.email_verification_token = None
            user.email_verification_sent_at = None
            user.save(update_fields=['is_active', 'email_verification_token', 'email_verification_sent_at'])
            return Response({'status': 'success', 'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error during email verification: {str(e)}", exc_info=True)
            return Response({'status': 'error', 'message': 'Verification failed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResendEmailView(APIView):
    """
    API view to resend the email verification link.
    """
    permission_classes = [AllowAny]
    throttle_scope = "resend_email"
    throttle_classes = [ScopedRateThrottle]

    def post(self, request):
        serializer = ResendEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data["user_id"]
        new_email = serializer.validated_data.get("email")
        token = serializer.validated_data.get("token")

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "If the account exists, a verification email has been sent."},
                status=status.HTTP_202_ACCEPTED,
            )

        if new_email:
            normalized_email = new_email.strip().lower()
            user.pending_email = normalized_email
            try:
                user.save(update_fields=["pending_email"])
            except IntegrityError:
                logger.warning(f"Failed to update pending_email for user {user.user_id}: email already exists")

        email_to_send = user.pending_email or user.email
        if not email_to_send:
            logger.warning(f"User {user.user_id} has no valid email to send verification to.")
            return Response(
                {"detail": "Unable to send verification email due to missing email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not token:
            token = EMAIL_VERIFICATION_TOKEN.make_token(user)

        verification_relative_url = reverse(
            'verify-email', kwargs={'user_id': user.user_id, 'token': token}
        )
        verify_url = f"{settings.FRONTEND_URL}{verification_relative_url}"

        context = {
            'user': user,
            'verification_url': verify_url,
            'user_display_name': user.first_name or user.email,
            'support_text': SUPPORT_TEXT,
        }

        subject = "Confirm your email"
        html_message = render_to_string(ACTIVATION_EMAIL_TEMPLATE, context)
        plain_message = (
            f"Hello {context['user_display_name']},\n\n"
            f"Please verify your email by clicking the link below:\n{verify_url}\n\n"
            f"{context['support_text']}"
        )

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_to_send],
                html_message=html_message,
                fail_silently=False,
            )
        except (ImproperlyConfigured, SMTPException):
            logger.critical(
                f"Verification email send failed to {email_to_send}",
                exc_info=True
            )
            return Response(
                {"detail": "Internal server configuration error."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except Exception as e:
            logger.error(
                f"Verification email send failed to {email_to_send}: {e}",
                exc_info=True
            )
            return Response(
                {"detail": "If the account exists, a verification email has been sent."},
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(
            {"detail": "If the account exists, a verification email has been sent."},
            status=status.HTTP_202_ACCEPTED,
        )


def error_response(message, status_code):
    if isinstance(message, str):
        data = {"detail": message}
    else:
        data = message
    return Response(data, status=status_code)


class CustomPasswordResetView(APIView):
    """Handle password reset requests."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return error_response({"email": "User with this email was not found."}, status.HTTP_404_NOT_FOUND)

        PasswordResetEmail(request, {"user": user}).send([user.email])
        return Response({"detail": "Password reset instructions sent."}, status=status.HTTP_200_OK)


class CustomPasswordResetConfirmView(APIView):
    """Confirm password reset with token."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        user = serializer.context['user']
        new_password = serializer.validated_data['new_password']

        # Reviewer fix: catch only the specific validation error instead of broad Exception
        try:
            validate_password(new_password, user)
        except DjangoValidationError as e:
            return error_response({"new_password": list(e.messages)}, status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)


class TokenBlacklistView(APIView):
    """Logout by blacklisting refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"detail": "Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Token successfully blacklisted."}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}", exc_info=True)
            return Response({"detail": "Failed to blacklist token."}, status=status.HTTP_400_BAD_REQUEST)


def get_default_user_role():
    """
    Retrieve the default 'user' role with caching and error handling.
    """
    cache_key = "default_user_role"
    default_role = cache.get(cache_key)

    if default_role is None:
        try:
            default_role = UserRole.objects.get(role="user")
            cache.set(cache_key, default_role, timeout=3600)  # Cache for 1 hour
        except UserRole.DoesNotExist:
            raise RuntimeError(
                "Default 'user' role is not configured in the system. "
                "Please create a UserRole with role='user'."
            )

    return default_role


class OAuthTokenObtainPairView(TokenObtainPairView):
    """
    Extended token authentication endpoint that supports OAuth provider authentication (Google/GitHub).
    Endpoint: users/oauth/login/
    Methods: POST
    Request (OAuth): {"provider": "google|github", "access_token": "oauth_token"}
    """
    permission_classes = [AllowAny]  # Explicitly mark as public endpoint
    throttle_classes = [AnonRateThrottle]  # Prevent brute-force attacks

    def post(self, request, *args, **kwargs):
        provider = request.data.get('provider')  # 'google' or 'github'
        access_token = request.data.get('access_token')

        if provider and access_token:
            if isinstance(provider, str) and isinstance(access_token, str):
                provider = provider.lower().strip()  # Normalize provider
                return self.handle_oauth(provider, access_token)
            else:
                return Response(
                    {"error": "Invalid provider or access_token type"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"error": "Provider or Access_token is missing"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def handle_oauth(self, provider, access_token):
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
        """
        google_userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(google_userinfo_url, headers=headers, timeout=(3.05, 10))
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.Timeout as e:
            logger.error("Google OAuth timeout", extra={'error_type': 'timeout', 'timeout': str(e), 'provider': 'google'})
            return Response(
                {"error": "Google API timeout", "detail": "The connection to Google's servers timed out", "resolution": "Please try again later"},
                status=status.HTTP_408_REQUEST_TIMEOUT
            )

        except requests.exceptions.SSLError:
            logger.error("Google OAuth SSL verification failed")
            return Response(
                {"error": "Security verification failed", "detail": "Could not establish secure connection to Google", "resolution": "Try again or contact support"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        except requests.exceptions.ConnectionError:
            logger.error("Google OAuth connection failed")
            return Response(
                {"error": "Connection failed", "detail": "Network issues contacting Google's servers", "resolution": "Check your internet connection"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        except requests.exceptions.RequestException as e:
            response_data = {}
            # Reviewer fix: hasattr check is enough; no need for 'is not None'
            if hasattr(e, 'response'):
                try:
                    response_data = e.response.json()
                except ValueError:
                    response_data = {'raw_response': str(e.response.content)}

            logger.error(
                "Google OAuth token validation failed",
                extra={
                    'error_type': 'token_validation',
                    'http_status': getattr(e.response, 'status_code', None),
                    'response': response_data,
                    'provider': 'google'
                }
            )

            return Response(
                {"error": "Invalid Google token", "detail": "The provided access token was rejected by Google", "resolution": "Re-authenticate with Google"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(data, dict):
            return Response({"error": f"Expected JSON object, got {type(data).__name__}"}, status=status.HTTP_400_BAD_REQUEST)

        email = data.get("email")
        if not email:
            return Response(
                {"error": ("Email not provided by OAuth provider. "
                           "Ensure email access is requested in the provider's scope.")},
                status=status.HTTP_400_BAD_REQUEST
            )

        first_name = data.get("given_name", "")
        last_name = data.get("family_name", "")

        user, _ = self.get_or_create_user(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "password": "",
                "user_phone": "",
                "title": "",
                "role": get_default_user_role()
            },
            provider="google"
        )

        return self.generate_jwt_response(user)

    def handle_github_oauth(self, access_token):
        """
        Authenticate using GitHub OAuth access token.
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        try:
            user_response = requests.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=(3.05, 10)
            )
            user_response.raise_for_status()
            user_data = user_response.json()

            email_response = requests.get(
                "https://api.github.com/user/emails",
                headers=headers,
                timeout=(3.05, 5)
            )
            email_response.raise_for_status()
            emails = email_response.json()

            primary_email = next((e for e in emails if e.get("primary")), None)

            if not primary_email:
                logger.warning(
                    "GitHub OAuth missing verified primary email",
                    extra={
                        'available_emails': [
                            {'email': e.get('email'), 'verified': e.get('verified')}
                            for e in emails if isinstance(e, dict)
                        ],
                        'github_id': user_data.get('id')
                    }
                )
                return Response(
                    {
                        "error": "Email not provided by GitHub",
                        "detail": (
                            "No verified primary email found on GitHub account. "
                            "Users must have a verified primary email to authenticate."
                        ),
                        "resolution": [
                            "1. Check email settings at: https://github.com/settings/emails",
                            "2. Verify at least one email address",
                            "3. Set one as primary"
                        ],
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            email = primary_email['email']

            full_name = (user_data.get("name") or "").strip()
            name_parts = full_name.split(" ", 1)
            first_name = name_parts[0][:150] if name_parts else ""
            last_name = name_parts[1][:150] if len(name_parts) > 1 else ""

            user, _ = self.get_or_create_user(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "password": "",
                    "user_phone": "",
                    "title": "",
                    "role": get_default_user_role()
                },
                provider="github"
            )

            return self.generate_jwt_response(user)

        except requests.Timeout:
            logger.error("GitHub API timeout")
            return Response(
                {"error": "GitHub API timeout", "detail": "Connection to GitHub servers timed out", "resolution": "Please try again later"},
                status=status.HTTP_408_REQUEST_TIMEOUT
            )

        except requests.ConnectionError:
            logger.error("GitHub connection failed")
            return Response(
                {"error": "Network error", "detail": "Could not reach GitHub servers", "resolution": "Check your internet connection"},
                status=status.HTTP_502_BAD_GATEWAY
            )

        except requests.HTTPError as e:
            error_data = {}
            try:
                error_data = e.response.json()
            except ValueError:
                error_data = {'raw_response': str(e.response.content)}

            logger.error(
                "GitHub API error",
                extra={'status_code': e.response.status_code, 'error': error_data.get('message'), 'github_docs': error_data.get('documentation_url')}
            )

            if e.response.status_code == 401:
                return Response(
                    {"error": "Invalid GitHub token", "detail": "The access token was rejected", "resolution": "Re-authenticate with GitHub"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {"error": "GitHub API error", "detail": error_data.get('message', 'Unknown error'), "documentation": error_data.get('documentation_url')},
                    status=status.HTTP_502_BAD_GATEWAY
                )

        except Exception as e:
            logger.critical("Unexpected GitHub OAuth error", exc_info=True, extra={'error': str(e)})
            return Response({"error": "Authentication processing failed", "detail": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_or_create_user(self, email, defaults, provider):
        """
        Helper method to get or create user with intelligent field updates.
        """
        user, created = User.objects.get_or_create(email=email, defaults=defaults)

        if created:
            user.set_unusable_password()
            user.save()
            logger.info(
                f"User created via {provider} OAuth",
                extra={
                    'user_id': user.pk,
                    'email': email,
                    'provider': provider,
                    'action': 'user_creation',
                    'source': 'oauth',
                    'fields_created': {
                        'first_name': defaults.get("first_name"),
                        'last_name': defaults.get("last_name"),
                        'role': user.role.role if getattr(user, "role", None) else None
                    }
                }
            )
        else:
            update_fields = {}
            if defaults.get('first_name'):
                update_fields['first_name'] = defaults['first_name']
            if defaults.get('last_name'):
                update_fields['last_name'] = defaults['last_name']

            if update_fields:
                User.objects.filter(pk=user.pk).update(**update_fields)
                user.refresh_from_db()
                logger.info(
                    "User logged in via OAuth",
                    extra={
                        'user_id': user.pk,
                        'email': email,
                        'provider': provider,
                        'action': 'user_update',
                        'source': 'oauth',
                        'fields_updated': update_fields,
                        'changed_fields': list(update_fields.keys())
                    }
                )
        return user, created

    def generate_jwt_response(self, user):
        """
        Generate standardized JWT token response with user data.
        """
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data
        })

