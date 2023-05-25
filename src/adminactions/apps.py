from django.apps import AppConfig

from adminactions import config


class Config(AppConfig):
    name = 'adminactions'

    def ready(self):
        from adminactions import consts
        from .compat import celery_present  # noqa
        from . import checks  # noqa
        if celery_present:
            from . import tasks

        if config.AA_PERMISSION_HANDLER == consts.AA_PERMISSION_CREATE_USE_APPCONFIG:
            from .perms import create_extra_permissions
            create_extra_permissions()
