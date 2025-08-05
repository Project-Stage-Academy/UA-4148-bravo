import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from profiles.models import Startup, Investor
from profiles.serializers import StartupSerializer, InvestorSerializer

logger = logging.getLogger(__name__)


class StartupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Startup profiles.
    Includes filtering, searching, and validation logic.
    """
    queryset = Startup.objects.select_related('user', 'industry', 'location').prefetch_related('projects')
    serializer_class = StartupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['industry', 'stage', 'is_participant', 'country']
    search_fields = ['company_name', 'contact_person', 'email']

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        try:
            instance.clean()
            instance.save()
            logger.info(f"Startup created: {instance}")
        except DjangoValidationError as e:
            logger.warning(f"Validation error during creation: {e}")
            raise DRFValidationError(e.message_dict)

    def perform_update(self, serializer):
        instance = serializer.save()
        try:
            instance.clean()
            instance.save()
            logger.info(f"Startup updated: {instance}")
        except DjangoValidationError as e:
            logger.warning(f"Validation error during update: {e}")
            raise DRFValidationError(e.message_dict)


class InvestorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Investor profiles.
    """
    queryset = Investor.objects.select_related('user', 'industry', 'location')
    serializer_class = InvestorSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        try:
            instance.clean()
            instance.save()
            logger.info(f"Investor created: {instance}")
        except DjangoValidationError as e:
            logger.warning(f"Validation error during creation: {e}")
            raise DRFValidationError(e.message_dict)

    def perform_update(self, serializer):
        instance = serializer.save()
        try:
            instance.clean()
            instance.save()
            logger.info(f"Investor updated: {instance}")
        except DjangoValidationError as e:
            logger.warning(f"Validation error during update: {e}")
            raise DRFValidationError(e.message_dict)


