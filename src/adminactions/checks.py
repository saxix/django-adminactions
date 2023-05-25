from celery.app.control import Control, Inspect
from django.core.checks import Error, register

from adminactions.compat import celery_present


@register()
def check_adminactions_settings(app_configs, **kwargs):
    errors = []
    from .config import AA_PERMISSION_HANDLER
    from .consts import (AA_PERMISSION_CREATE_USE_APPCONFIG,
                         AA_PERMISSION_CREATE_USE_COMMAND,
                         AA_PERMISSION_CREATE_USE_SIGNAL,)

    if AA_PERMISSION_HANDLER not in [AA_PERMISSION_CREATE_USE_APPCONFIG,
                                     AA_PERMISSION_CREATE_USE_SIGNAL,
                                     AA_PERMISSION_CREATE_USE_COMMAND]:
        errors.append(
            Error(
                'Invalid value for settings.AA_PERMISSION_HANDLER',
                hint='use one of [api.AA_PERMISSION_CREATE_USE_SIGNAL, '
                     'api.AA_PERMISSION_CREATE_USE_APPCONFIG, api.AA_PERMISSION_CREATE_USE_COMMAND]',
                obj='settings.AA_PERMISSION_HANDLER',
                id='adminactions.E001',
            )
        )
    return errors
