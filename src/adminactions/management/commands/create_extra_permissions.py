from typing import Any

from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> None:  # noqa: PLR6301, ARG002
        from adminactions.perms import create_extra_permissions  # noqa: PLC0415

        create_extra_permissions()
