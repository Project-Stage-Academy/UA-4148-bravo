from django.db import migrations


def create_initial_notification_types(apps, schema_editor):
    """Create initial notification types."""
    NotificationType = apps.get_model('communications', 'NotificationType')
    
    # List of notification types to create
    notification_types = [
        {
            'code': 'startup_saved',
            'name': 'Startup Saved',
            'description': 'Notification when a user saves a startup to their favorites',
            'default_frequency': 'immediate',
            'is_active': True
        },
        {
            'code': 'project_followed',
            'name': 'Project Followed',
            'description': 'Notification when a user follows a project',
            'default_frequency': 'immediate',
            'is_active': True
        },
        {
            'code': 'message_received',
            'name': 'Message Received',
            'description': 'Notification when a user receives a new message',
            'default_frequency': 'immediate',
            'is_active': True
        },
        {
            'code': 'project_updated',
            'name': 'Project Updated',
            'description': 'Notification when a followed project is updated',
            'default_frequency': 'daily_digest',
            'is_active': True
        },
    ]
    
    # Create notification types
    for nt_data in notification_types:
        NotificationType.objects.get_or_create(
            code=nt_data['code'],
            defaults={
                'name': nt_data['name'],
                'description': nt_data['description'],
                'default_frequency': nt_data['default_frequency'],
                'is_active': nt_data['is_active']
            }
        )


def delete_notification_types(apps, schema_editor):
    """Delete all notification types."""
    NotificationType = apps.get_model('communications', 'NotificationType')
    NotificationType.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('communications', '0002_create_initial_notification_types'),
    ]

    operations = [
        migrations.RunPython(
            create_initial_notification_types,
            reverse_code=delete_notification_types
        ),
    ]
