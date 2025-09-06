from django_filters import FilterSet, CharFilter, NumberFilter
from .models import Investor

class InvestorFilter(FilterSet):
    """
    FilterSet for Investor model supporting industry, stage,
    team size, and fund size filtering.
    """
    industry = CharFilter(field_name="industry__name", lookup_expr="iexact")
    stage = CharFilter(field_name="stage", lookup_expr="iexact")
    min_team_size = NumberFilter(field_name="team_size", lookup_expr="gte")
    max_team_size = NumberFilter(field_name="team_size", lookup_expr="lte")
    min_fund_size = NumberFilter(field_name="fund_size", lookup_expr="gte")
    max_fund_size = NumberFilter(field_name="fund_size", lookup_expr="lte")

    class Meta:
        model = Investor
        fields = [
            "industry", "stage", "min_team_size", "max_team_size",
            "min_fund_size", "max_fund_size"
        ]
