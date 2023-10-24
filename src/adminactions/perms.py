from django.apps import apps

__all__ = ["create_extra_permissions", "get_permission_codename"]


def get_permission_codename(action, opts):
    return "%s_%s" % (action, opts.object_name.lower())


def get_contenttype_for_model(model):
    from django.contrib.contenttypes.models import ContentType

    model = model._meta.concrete_model
    opts = model._meta
    ct, __ = ContentType.objects.get_or_create(
        app_label=opts.app_label,
        model=opts.model_name,
    )
    return ct


def create_extra_permissions():
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    from .actions import actions as aa

    perm_suffix = "adminactions_"
    existing_perms = set(
        Permission.objects.filter(codename__startswith=perm_suffix).values_list("codename", "content_type_id")
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
                action.base_permission.replace(perm_suffix, ""), opts.verbose_name_raw
            )
            permission = Permission(codename=codename, content_type=ct, name=label[:255])
            new_permissions.append(permission)

    Permission.objects.bulk_create(new_permissions, ignore_conflicts=True)
