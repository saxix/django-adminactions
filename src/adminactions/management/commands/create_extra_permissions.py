from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        from adminactions.perms import create_extra_permissions
        create_extra_permissions()
