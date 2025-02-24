from django.apps import AppConfig

from adminactions import config, consts


class Config(AppConfig):
    name = "adminactions"

    def ready(self) -> None:  # noqa: PLR6301,
        from . import checks  # noqa: F401, PLC0415
        from .compat import celery_present  # noqa: PLC0415

        if celery_present:
            from . import tasks  # noqa: F401, PLC0415

        if config.AA_PERMISSION_HANDLER == consts.AA_PERMISSION_CREATE_USE_APPCONFIG:
            from .perms import create_extra_permissions  # noqa: PLC0415

            create_extra_permissions()
