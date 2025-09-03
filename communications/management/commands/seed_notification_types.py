from django.core.management.base import BaseCommand

from communications.models import NotificationType, NotificationFrequency
from common.enums import NotificationTypeCode


class Command(BaseCommand):
    help = "Seed canonical NotificationType rows (idempotent upsert)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        # Keep this in sync with common.enums.NotificationTypeCode
        canonical_types = [
            {
                "code": NotificationTypeCode.STARTUP_SAVED.value,
                "name": NotificationTypeCode.STARTUP_SAVED.label,
                "description": "An investor saved your startup profile.",
                "default_frequency": NotificationFrequency.IMMEDIATE,
            },
            {
                "code": NotificationTypeCode.PROJECT_FOLLOWED.value,
                "name": NotificationTypeCode.PROJECT_FOLLOWED.label,
                "description": "An investor followed your project.",
                "default_frequency": NotificationFrequency.IMMEDIATE,
            },
            {
                "code": NotificationTypeCode.MESSAGE_RECEIVED.value,
                "name": NotificationTypeCode.MESSAGE_RECEIVED.label,
                "description": "You received a new message.",
                "default_frequency": NotificationFrequency.IMMEDIATE,
            },
            {
                "code": NotificationTypeCode.ACTIVITY_SUMMARIZED.value,
                "name": NotificationTypeCode.ACTIVITY_SUMMARIZED.label,
                "description": "Your weekly activity summary is ready.",
                "default_frequency": NotificationFrequency.WEEKLY_SUMMARY,
            },
        ]

        created_count = 0
        updated_count = 0

        for item in canonical_types:
            code = item["code"]
            name = item["name"]
            description = item["description"]
            default_frequency = item["default_frequency"]

            existing = NotificationType.objects.filter(code=code).first()
            if not existing:
                if dry_run:
                    self.stdout.write(self.style.WARNING(f"(dry-run) Would create NotificationType: {code}"))
                else:
                    NotificationType.objects.create(
                        code=code,
                        name=name,
                        description=description,
                        default_frequency=default_frequency,
                    )
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Created NotificationType: {code}"))
                continue

            # Upsert fields if changed (do not touch is_active to respect admin choice)
            changed_fields = {}
            if existing.name != name:
                changed_fields["name"] = name
            if (existing.description or "") != (description or ""):
                changed_fields["description"] = description
            if existing.default_frequency != default_frequency:
                changed_fields["default_frequency"] = default_frequency

            if changed_fields:
                updated_count += 1
                if dry_run:
                    self.stdout.write(self.style.WARNING(f"(dry-run) Would update {code}: {', '.join(changed_fields.keys())}"))
                else:
                    for field, value in changed_fields.items():
                        setattr(existing, field, value)
                    existing.save(update_fields=[*changed_fields.keys(), "updated_at"])
                    self.stdout.write(self.style.SUCCESS(f"Updated NotificationType: {code}"))
            else:
                self.stdout.write(f"No changes for NotificationType: {code}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created: {created_count}, Updated: {updated_count}."
            )
        )