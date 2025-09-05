from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Create all default data: users, startups, projects, investors, communications"

    def handle(self, *args, **options):
        commands = [
            "create_users",
            "create_default_startups",
            "create_default_projects",
            "create_default_investors",
            "create_default_communications",
        ]

        for command in commands:
            try:
                call_command(command)
                self.stdout.write(self.style.SUCCESS(f"Successfully ran {command}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to run {command}: {e}"))
