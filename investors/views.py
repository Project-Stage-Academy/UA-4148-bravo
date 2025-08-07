import logging
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from investors.models import Investor
from investors.serializers import InvestorSerializer

logger = logging.getLogger(__name__)


class InvestorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Investor investors.
    Optimized to avoid N+1 queries when accessing startup_details.
    """
    queryset = Investor.objects.select_related('user', 'industry', 'location') \
        .prefetch_related('startups__industry')
    serializer_class = InvestorSerializer
    permission_classes = [IsAuthenticated]
