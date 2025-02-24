from typing import TYPE_CHECKING

from django.apps import apps
from django.db.models.options import Options

if TYPE_CHECKING:
    from django.contrib.contenttypes.models import ContentType

__all__ = ["create_extra_permissions", "get_permission_codename"]

from django.db.models.base import Model


def get_permission_codename(action: str, opts: Options) -> str:
    return f"{action}_{opts.object_name.lower()}"


def get_contenttype_for_model(model: Model) -> "ContentType":
    from django.contrib.contenttypes.models import ContentType  # noqa: PLC0415

    opts = model._meta.concrete_model._meta
    ct, __ = ContentType.objects.get_or_create(
        app_label=opts.app_label,
        model=opts.model_name,
    )
    return ct


def create_extra_permissions() -> None:
    from django.contrib.auth.models import Permission  # noqa: PLC0415
    from django.contrib.contenttypes.models import ContentType  # noqa: PLC0415

    from .actions import actions as aa  # noqa: PLC0415

    perm_suffix = "adminactions_"
    existing_perms = set(
        Permission.objects.filter(codename__startswith=perm_suffix).values_list("codename", "content_type_id"),
    )
    models = list(apps.get_models())
    content_types = ContentType.objects.get_for_models(*models)
    # https://github.com/saxix/django-adminactions/issues/199
    ContentType.objects.bulk_create(content_types.values(), ignore_conflicts=True)

    new_permissions = []
    for model in models:
        for action in aa:
            opts = model._meta
            codename = get_permission_codename(action.base_permission, opts)[:100]
            ct = content_types[model]
            if (codename, ct.id) in existing_perms:
                continue
            label = "Can {} {} (adminactions)".format(
                action.base_permission.replace(perm_suffix, ""),
                opts.verbose_name_raw,
            )
            permission = Permission(codename=codename, content_type=ct, name=label[:255])
            new_permissions.append(permission)

    Permission.objects.bulk_create(new_permissions, ignore_conflicts=True)
