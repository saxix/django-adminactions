from django.apps import apps
from django.conf import settings

from .consts import AA_PERMISSION_CREATE_USE_SIGNAL

AA_PERMISSION_HANDLER = getattr(settings, 'AA_PERMISSION_HANDLER', AA_PERMISSION_CREATE_USE_SIGNAL)

__all__ = ["create_extra_permissions"]


def get_permission_codename(action, opts):
    return '%s_%s' % (action, opts.object_name.lower())


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

    from .actions import actions as aa

    for model in apps.get_models():
        ct = get_contenttype_for_model(model)
        for action in aa:
            opts = model._meta
            codename = get_permission_codename(action.base_permission, opts)
            label = 'Can {} {} (adminactions)'.format(action.base_permission.replace('adminactions_', ""),
                                                      opts.verbose_name_raw)
            params = dict(codename=codename,
                          content_type=ct,
                          defaults={'name': label[:50]})
            Permission.objects.get_or_create(**params)
