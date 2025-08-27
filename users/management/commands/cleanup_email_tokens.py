from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import User

class Command(BaseCommand):
    help = 'Clean up expired email verification tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to consider a token as expired (default: 7)'
        )

    def handle(self, *args, **options):
        days = options['days']
        expiration_date = timezone.now() - timezone.timedelta(days=days)
        
        expired_users = User.objects.filter(
            email_verification_sent_at__lt=expiration_date,
            is_active=False
        ).exclude(email_verification_token__isnull=True)
        
        count = expired_users.count()
        
        if count > 0:
            updated = expired_users.update(
                email_verification_token=None,
                email_verification_sent_at=None
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleaned up {updated} expired email verification tokens')
            )
        else:
            self.stdout.write('No expired email verification tokens found')
