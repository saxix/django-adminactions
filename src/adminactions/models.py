from django.db.models.signals import post_migrate

from . import config, consts, perms


def create_extra_permissions_handler(sender, **kwargs):
    global TOTAL_MODELS, COUNTER
    if config.AA_PERMISSION_HANDLER == consts.AA_PERMISSION_CREATE_USE_SIGNAL:
        perms.create_extra_permissions()
    else:
        post_migrate.disconnect(dispatch_uid="adminactions.create_extra_permissions")


post_migrate.connect(
    create_extra_permissions_handler,
    dispatch_uid="adminactions.create_extra_permissions",
)
