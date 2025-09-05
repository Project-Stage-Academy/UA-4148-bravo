import django_filters as df
from startups.models import Startup

class StartupFilter(df.FilterSet):
    industry = df.CharFilter(method='filter_industry')
    industry_name = df.CharFilter(field_name='industry__name', lookup_expr='iexact')
    country = df.CharFilter(field_name='location__country', lookup_expr='iexact')
    city = df.CharFilter(field_name='location__city', lookup_expr='iexact')
    min_team_size = df.NumberFilter(field_name='team_size', lookup_expr='gte')
    funding_needed_lte = df.NumberFilter(field_name='funding_needed', lookup_expr='lte')
    is_verified = df.BooleanFilter(field_name='is_verified')
    stage = df.CharFilter(field_name='stage', lookup_expr='iexact')

    def filter_industry(self, qs, name, value):
        if str(value).isdigit():
            return qs.filter(industry_id=int(value))
        return qs.filter(industry__name__iexact=value)
    
    class Meta:
        model = Startup
        fields = [
            'industry', 'industry_name', 'country', 'city',
            'is_verified', 'min_team_size', 'funding_needed_lte', 'stage'
        ]
