from typing import Any

from django.db.models.base import Model
from django.db.models.signals import post_migrate

from . import config, consts, perms


def create_extra_permissions_handler(sender: Model, **kwargs: Any) -> None:  # noqa: ARG001
    if config.AA_PERMISSION_HANDLER == consts.AA_PERMISSION_CREATE_USE_SIGNAL:
        perms.create_extra_permissions()
    else:
        post_migrate.disconnect(dispatch_uid="adminactions.create_extra_permissions")


post_migrate.connect(
    create_extra_permissions_handler,
    dispatch_uid="adminactions.create_extra_permissions",
)
