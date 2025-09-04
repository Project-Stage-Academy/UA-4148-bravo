from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Create all default data: users, startups, projects, investors, communications"

    def handle(self, *args, **options):
        call_command("create_users")
        call_command("create_default_startups")
        call_command("create_default_projects")
        call_command("create_default_investors")
        call_command("create_default_communications")
        self.stdout.write(self.style.SUCCESS("All default data created successfully"))