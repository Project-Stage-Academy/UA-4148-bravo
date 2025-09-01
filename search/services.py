from startups.models import Startup
from django.db.models import Q


def filter_startups(query: str):
    """
    Basic search function for startups.
    Case-insensitive, partial match by company_name or description.
    """
    if not query:
        return Startup.objects.none()

    return Startup.objects.filter(
        Q(company_name__icontains=query) |
        Q(description__icontains=query)
    ).select_related("location", "industry")
