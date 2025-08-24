import traceback
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.core.exceptions import ValidationError
from common.enums import Stage
from investors.models import Investor
from startups.models import Location, Industry, Startup
import datetime
import logging
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from users.serializers.company_bind_serializer import CompanyBindingSerializer
from django_countries.fields import Country

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Bind user to company",
    description="Authenticated users can bind to existing companies or create new ones",
    request={
        'application/json': {
            'type': 'object',
            'required': ['company_name', 'company_type'],
            'properties': {
                'company_name': {
                    'type': 'string',
                    'maxLength': 254,
                    'example': "Tech Innovations Inc."
                },
                'company_type': {
                    'type': 'string',
                    'enum': ['startup', 'investor'],
                    'example': "startup"
                },
            },
        }
    },
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description='Bound to existing company',
            examples=[
                OpenApiExample(
                    'Success response',
                    value={
                        "message": "Successfully bound to existing startup: Tech Innovations Inc.",
                        "company_type": "startup",
                        "company_id": 1
                    }
                )
            ]
        ),
        201: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description='Created and bound to new company',
            examples=[
                OpenApiExample(
                    'Success response',
                    value={
                        "message": "Successfully created and bound to new startup: Tech Innovations Inc.",
                        "company_type": "startup",
                        "company_id": 1
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description='Validation error',
            examples=[
                OpenApiExample(
                    'Error response',
                    value={"error": "User is already bound to a company."}
                )
            ]
        ),
        401: OpenApiResponse(description='Authentication required'),
        500: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description='Server error',
            examples=[
                OpenApiExample(
                    'Error response',
                    value={"error": "An unexpected error occurred."}
                )
            ]
        )
    },
    tags=["Authentication"],
    auth=[{'Bearer': []}]
)
class CompanyBindingView(APIView):
    """
    API endpoint for binding users to companies after registration.

    Allows authenticated users to associate themselves with either:
    1. An existing company (startup or investor)
    2. A newly created company if no matching company exists

    POST data format:
    {
        "company_name": "Company Name",
        "company_type": "startup"  # or "investor"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handle company binding request.

        Args:
            request: HTTP request containing company_name and company_type

        Returns:
            Response with binding result or error details
        """
        serializer = CompanyBindingSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        company_name = serializer.validated_data['company_name']
        company_type = serializer.validated_data['company_type']
        user = request.user

        if self._is_user_bound_to_company(user):
            return Response(
                {"error": "User is already bound to a company."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                if company_type == 'startup':
                    return self._bind_to_startup(user, company_name)
                else:
                    return self._bind_to_investor(user, company_name)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Company binding error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response(
                {"error": "An unexpected error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _is_user_bound_to_company(self, user):
        """
        Check if user is already associated with any company.

        Args:
            user: User instance to check

        Returns:
            bool: True if user is bound to a company, False otherwise
        """
        return getattr(user, 'startup', None) is not None or getattr(user, 'investor', None) is not None

    def _bind_to_startup(self, user, company_name):
        """
        Bind user to an existing or new startup.

        Args:
            user: User instance to bind
            company_name: Name of the startup

        Returns:
            Response with binding result
        """
        try:
            startup = Startup.objects.get(company_name__iexact=company_name)

            if startup.user is not None:
                return Response(
                    {"error": "Startup is already associated with another user."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                startup.user = user
                startup.save()
            except Exception as e:
                logger.error(f"Failed to save startup: {str(e)}")
                raise ValidationError(f"Failed to update startup: {str(e)}")

            return Response({
                "message": f"Successfully bound to existing startup: {startup.company_name}",
                "company_type": "startup",
                "company_id": startup.id
            }, status=status.HTTP_200_OK)

        except Startup.DoesNotExist:
            startup = self._create_new_startup(user, company_name)

            return Response({
                "message": f"Successfully created and bound to new startup: {company_name}",
                "company_type": "startup",
                "company_id": startup.id
            }, status=status.HTTP_201_CREATED)

    def _bind_to_investor(self, user, company_name):
        """
        Bind user to an existing or new investor.

        Args:
            user: User instance to bind
            company_name: Name of the investor

        Returns:
            Response with binding result
        """
        try:
            investor = Investor.objects.get(company_name__iexact=company_name)

            if investor.user is not None:
                return Response(
                    {"error": "Investor is already associated with another user."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                investor.user = user
                investor.save()
            except Exception as e:
                logger.error(f"Failed to save investor: {str(e)}")
                raise ValidationError(f"Failed to update investor: {str(e)}")

            return Response({
                "message": f"Successfully bound to existing investor: {investor.company_name}",
                "company_type": "investor",
                "company_id": investor.id
            }, status=status.HTTP_200_OK)

        except Investor.DoesNotExist:
            investor = self._create_new_investor(user, company_name)

            return Response({
                "message": f"Successfully created and bound to new investor: {company_name}",
                "company_type": "investor",
                "company_id": investor.id
            }, status=status.HTTP_201_CREATED)

    def _create_default_industry_and_location(self):
        """
        Create or get default industry and location instances.
        """
        industry, _ = Industry.objects.get_or_create(
            name="Unknown",
            defaults={'description': 'Default unknown industry'}
        )

        default_country = Country('US')

        location, _ = Location.objects.get_or_create(
            city="Unknown",
            country=default_country,
            defaults={
                'region': 'Unknown',
                'address_line': 'Default address',
                'postal_code': '00000'
            }
        )

        return industry, location

    def _create_new_startup(self, user, company_name):
        """
        Create a new startup instance with default values.

        Args:
            user: User to associate with the startup
            company_name: Name of the startup

        Returns:
            Startup instance
        """
        industry, location = self._create_default_industry_and_location()

        return Startup.objects.create(
            user=user,
            company_name=company_name,
            industry=industry,
            location=location,
            email=user.email,
            founded_year=datetime.datetime.now().year,
            team_size=1,
            stage=Stage.IDEA
        )

    def _create_new_investor(self, user, company_name):
        """
        Create a new investor instance with default values.

        Args:
            user: User to associate with the investor
            company_name: Name of the investor

        Returns:
            Investor instance
        """
        industry, location = self._create_default_industry_and_location()

        return Investor.objects.create(
            user=user,
            company_name=company_name,
            industry=industry,
            location=location,
            email=user.email,
            founded_year=datetime.datetime.now().year,
            team_size=1,
            stage=Stage.MVP,
            fund_size=0
        )
