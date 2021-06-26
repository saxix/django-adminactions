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
    for model in apps.get_models():
        for action in ('adminactions_export', 'adminactions_massupdate',
                       'adminactions_merge', 'adminactions_chart',
                       'adminactions_byrowsupdate'):
            opts = model._meta
            codename = get_permission_codename(action, opts)
            label = 'Can {} {} (adminactions)'.format(action.replace('adminactions_', ""),
                                                      opts.verbose_name_raw)
            ct = ContentType.objects.get_for_model(model)
            params = dict(codename=codename,
                          content_type=ct,
                          defaults={'name': label[:50]})
            Permission.objects.get_or_create(**params)
