from __future__ import absolute_import, unicode_literals
from django.db.models import signals


def get_permission_codename(action, opts):
    return '%s_%s' % (action, opts.object_name.lower())


def get_models(sender):
    """Handles deprecation of django.db.models.loading in Django1.9"""

    try:
        from django.apps import apps
        return [m for m in apps.get_models() if sender.__name__ in str(m)]
    except ImportError:
        # Default to django.db.models.loading when Django version < 1.7
        from django.db.models.loading import get_models
        return get_models(sender)


def create_extra_permission(sender, **kwargs):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    for model in get_models(sender):
        for action in ('adminactions_export', 'adminactions_massupdate', 'adminactions_merge'):
            opts = model._meta
            codename = get_permission_codename(action, opts)
            label = 'Can {} {} (adminactions)'.format(action.replace('adminactions_', ""), opts.verbose_name_raw)
            ct = ContentType.objects.get_for_model(model)
            Permission.objects.get_or_create(codename=codename, content_type=ct, defaults={'name': label[:50]})


signals.post_syncdb.connect(create_extra_permission)
