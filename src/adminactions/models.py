from __future__ import absolute_import, unicode_literals


def get_permission_codename(action, opts):
    return '%s_%s' % (action, opts.object_name.lower())


def get_models(app_config):
    """Handles deprecation of django.db.models.loading in Django1.9"""

    try:
        from django.apps import apps  # noqa

        return [m for m in app_config.get_models()]
    except ImportError:
        # Default to django.db.models.loading when Django version < 1.7
        from django.db.models.loading import get_models

        return get_models(app_config)


def create_extra_permission(sender, **kwargs):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    app_config = kwargs.get('app_config', sender)

    for model in get_models(app_config):
        for action in ('adminactions_export', 'adminactions_massupdate', 'adminactions_merge', 'adminactions_chart', 'adminactions_byrowsupdate'):
            opts = model._meta
            codename = get_permission_codename(action, opts)
            label = 'Can {} {} (adminactions)'.format(action.replace('adminactions_', ""), opts.verbose_name_raw)
            ct = ContentType.objects.get_for_model(model)
            Permission.objects.get_or_create(codename=codename, content_type=ct, defaults={'name': label[:50]})

# post_migrate = Signal(providing_args=["app_config", "verbosity", "interactive", "using"])
# post_syncdb = Signal(providing_args=["class", "app", "created_models", "verbosity", "interactive", "db"])


try:
    from django.db.models.signals import post_migrate

    post_migrate.connect(create_extra_permission)
except ImportError:
    from django.db.models.signals import post_syncdb

    post_syncdb.connect(create_extra_permission)
