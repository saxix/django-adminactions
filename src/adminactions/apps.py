from django.apps import AppConfig


class Config(AppConfig):
    name = 'adminactions'

    def ready(self):
        from . import checks  # noqa
        import adminactions.perms as p
        from django.conf import settings
        p.AA_PERMISSION_HANDLER = getattr(settings, 'AA_PERMISSION_HANDLER',
                                          p.AA_PERMISSION_CREATE_USE_SIGNAL)

        if p.AA_PERMISSION_HANDLER == p.AA_PERMISSION_CREATE_USE_APPCONFIG:
            from .perms import create_extra_permissions
            create_extra_permissions()
