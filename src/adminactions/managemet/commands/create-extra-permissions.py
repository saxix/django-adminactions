from django.core.management import call_command, BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        from adminactions.models import create_extra_permission
        create_extra_permission(None)
