from django.core.checks import Error, register


@register()
def check_adminactions_settings(app_configs, **kwargs):
    errors = []
    from .config import AA_PERMISSION_HANDLER
    from .consts import (
        AA_PERMISSION_CREATE_USE_APPCONFIG,
        AA_PERMISSION_CREATE_USE_COMMAND,
        AA_PERMISSION_CREATE_USE_SIGNAL,
    )

    if AA_PERMISSION_HANDLER not in [
        AA_PERMISSION_CREATE_USE_APPCONFIG,
        AA_PERMISSION_CREATE_USE_SIGNAL,
        AA_PERMISSION_CREATE_USE_COMMAND,
    ]:
        errors.append(
            Error(
                "Invalid value for settings.AA_PERMISSION_HANDLER",
                hint="use one of [api.AA_PERMISSION_CREATE_USE_SIGNAL, "
                "api.AA_PERMISSION_CREATE_USE_APPCONFIG, api.AA_PERMISSION_CREATE_USE_COMMAND]",
                obj="settings.AA_PERMISSION_HANDLER",
                id="adminactions.E001",
            )
        )
    return errors


#
# @register()
# def check_celery_config(app_configs, **kwargs):
#     errors = []
#     if celery_present:
#         from celery import current_app
#         c: Control = current_app.control
#         i: Inspect = c.inspect()
#         print("adminactions/checks.py: 37", i.registered_tasks())
#     return errors
