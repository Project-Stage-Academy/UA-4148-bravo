from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    NotificationType,
    UserNotificationPreference,
    UserNotificationTypePreference
)


class NotificationTypeAdmin(admin.ModelAdmin):
    """Admin interface for NotificationType model."""
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('created_at', 'updated_at')
    def get_fieldsets(self, request, obj=None):
        main_fields = [f.name for f in self.model._meta.get_fields() 
                      if f.name not in ('id', 'created_at', 'updated_at')]
        
        return (
            (None, {
                'fields': main_fields
            }),
            (_('Timestamps'), {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )


class UserNotificationTypePreferenceInline(admin.TabularInline):
    """Inline admin for user notification type preferences."""
    model = UserNotificationTypePreference
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('notification_type', 'frequency', 'created_at', 'updated_at')


class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for UserNotificationPreference model."""
    list_display = ('user', 'enable_in_app', 'enable_email', 'enable_push', 'updated_at')
    list_filter = ('enable_in_app', 'enable_email', 'enable_push')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [UserNotificationTypePreferenceInline]
    
    def get_fieldsets(self, request, obj=None):
        user_fields = ['user']
        
        NOTIFICATION_CHANNELS = [
            'enable_in_app',
            'enable_email',
            'enable_push',
            # Add new notification channel fields here as they're added to the model
        ]
        
        other_fields = [f.name for f in self.model._meta.get_fields() 
                       if f.name not in user_fields + NOTIFICATION_CHANNELS + 
                       ['id', 'created_at', 'updated_at']]
        
        fieldsets = [
            (_('User'), {
                'fields': user_fields
            }),
            (_('Notification Channels'), {
                'fields': NOTIFICATION_CHANNELS
            }),
            (_('Timestamps'), {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        ]

        if other_fields:
            fieldsets.insert(1, (None, {
                'fields': other_fields
            }))
            
        return fieldsets


admin.site.register(NotificationType, NotificationTypeAdmin)
admin.site.register(UserNotificationPreference, UserNotificationPreferenceAdmin)
