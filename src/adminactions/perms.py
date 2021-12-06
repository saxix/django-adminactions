from django.apps import apps
from django.conf import settings

AA_PERMISSION_CREATE_USE_SIGNAL = 1
AA_PERMISSION_CREATE_USE_APPCONFIG = 2
AA_PERMISSION_CREATE_USE_COMMAND = 3
AA_PERMISSION_HANDLER_VALUES = [AA_PERMISSION_CREATE_USE_SIGNAL,
                                AA_PERMISSION_CREATE_USE_APPCONFIG,
                                AA_PERMISSION_CREATE_USE_COMMAND]

AA_PERMISSION_HANDLER = getattr(settings, 'AA_PERMISSION_HANDLER', AA_PERMISSION_CREATE_USE_SIGNAL)


def get_permission_codename(action, opts):
    return '%s_%s' % (action, opts.object_name.lower())


def create_extra_permissions():
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    from .actions import actions as aa

    #  ('adminactions_export', 'adminactions_massupdate',
    #                        'adminactions_merge', 'adminactions_chart',
    #                        'adminactions_byrowsupdate')
    perm_suffix = 'adminactions_'
    existing_perms = set(
        Permission.objects.filter(codename__startswith=perm_suffix).values_list(
            'codename', 'content_type_id'
        )
    )
    models = list(apps.get_models())
    content_types = ContentType.objects.get_for_models(*models)

    new_permissions = []
    for model in models:
        for action in aa:
            opts = model._meta
            codename = get_permission_codename(action.base_permission, opts)[:100]
            ct = content_types[model]
            if (codename, ct.id) in existing_perms:
                continue
            label = 'Can {} {} (adminactions)'.format(action.base_permission.replace(perm_suffix, ""),
                                                      opts.verbose_name_raw)
            permission = Permission(codename=codename, content_type=ct, name=label[:255])
            new_permissions.append(permission)
    ContentType.objects.clear_cache()
    Permission.objects.bulk_create(new_permissions, ignore_conflicts=True)
