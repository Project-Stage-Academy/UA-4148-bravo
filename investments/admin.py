from django.contrib import admin
from investments.models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Subscription model.

    Makes the 'investment_share' field read-only to prevent manual edits,
    and displays key fields in the admin list view.
    """
    readonly_fields = ('investment_share',)
    list_display = ('investor', 'project', 'amount', 'investment_share', 'created_at')
    search_fields = ('investor__company_name', 'project__title')
    list_filter = ('created_at', 'project', 'investor')
    ordering = ('-created_at',)
