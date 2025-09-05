from django.contrib import admin
from .models import FollowedProject  # Import the FollowedProject model

# Register your models here.

@admin.register(FollowedProject)
class FollowedProjectAdmin(admin.ModelAdmin):
    """
    Admin interface for FollowedProject model.
    """
    list_display = ['investor', 'project', 'status', 'followed_at', 'created_at']
    list_filter = ['status', 'followed_at', 'created_at']
    search_fields = [
        'investor__company_name', 
        'investor__user__email',
        'project__title',
        'project__startup__company_name'
    ]
    readonly_fields = ['followed_at', 'created_at', 'updated_at']
    raw_id_fields = ['investor', 'project']
    
    fieldsets = (
        ('Relationship', {
            'fields': ('investor', 'project')
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes')
        }),
        ('Timestamps', {
            'fields': ('followed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'investor__user', 
            'project__startup'
        )
