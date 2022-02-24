from django.apps import AppConfig


class Config(AppConfig):
    name = 'adminactions'

    def ready(self):
        from django.conf import settings

        from adminactions import consts, perms

        from . import checks  # noqa
        perms.AA_PERMISSION_HANDLER = getattr(settings, 'AA_PERMISSION_HANDLER',
                                              consts.AA_PERMISSION_CREATE_USE_SIGNAL)

        if perms.AA_PERMISSION_HANDLER == consts.AA_PERMISSION_CREATE_USE_APPCONFIG:
            from .perms import create_extra_permissions
            create_extra_permissions()
