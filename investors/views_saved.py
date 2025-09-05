import django_filters
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from investors.models import SavedStartup
from investors.serializers import SavedStartupSerializer
from users.cookie_jwt import CookieJWTAuthentication
from users.permissions import IsAuthenticatedOr401, HasActiveCompanyAccount


class SavedStartupFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    saved_after = django_filters.IsoDateTimeFilter(field_name="saved_at", lookup_expr="gte")
    saved_before = django_filters.IsoDateTimeFilter(field_name="saved_at", lookup_expr="lte")

    class Meta:
        model = SavedStartup
        fields = ["status"]


class InvestorSavedStartupsList(generics.ListAPIView):
    """
    GET /api/investor/saved-startups/?status=watching&search=cool&ordering=-saved_at
    - returns ONLY the current investor's saved startups
    - filtering by status, saved_at range
    - search by startup name/email
    - ordering by saved_at, status, startup name
    """
    permission_classes = [IsAuthenticatedOr401, HasActiveCompanyAccount]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = SavedStartupSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = SavedStartupFilter
    search_fields = ["startup__company_name", "startup__email"]
    ordering_fields = ["saved_at", "status", "startup__company_name"]
    ordering = ["-saved_at"]

    def get_queryset(self):
        user = self.request.user
        investor = getattr(user, "investor", None)
        if not investor:
            raise PermissionDenied("Only investors can list saved startups.")
        return (
            SavedStartup.objects
            .select_related("startup", "investor")
            .filter(investor=investor)
        )


class UnsaveStartupView(generics.GenericAPIView):
    """
    DELETE /api/startups/<startup_id>/unsave/
    Idempotent: returns 200 with {"deleted": true/false}
    """
    permission_classes = [IsAuthenticatedOr401, HasActiveCompanyAccount]
    authentication_classes = [CookieJWTAuthentication]
    serializer_class = SavedStartupSerializer 

    def delete(self, request, startup_id: int):
        investor = getattr(request.user, "investor", None)
        if not investor:
            raise PermissionDenied("Only investors can unsave startups.")

        deleted_count, _ = SavedStartup.objects.filter(
            investor=investor,
            startup_id=startup_id,
        ).delete()

        return Response(
            {"startup_id": startup_id, "saved": False, "deleted": bool(deleted_count)},
            status=status.HTTP_200_OK,
        )

