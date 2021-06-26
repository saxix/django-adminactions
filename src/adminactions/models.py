# -*- coding: utf-8 -*-
from django.apps import apps
from django.db.models.signals import post_migrate, pre_migrate


def get_permission_codename(action, opts):
    return '%s_%s' % (action, opts.object_name.lower())


ALL_CONFIGS = False
COUNTER = 1


def collect_apps(sender, **kwargs):
    global ALL_CONFIGS, COUNTER
    ALL_CONFIGS = len(apps.get_app_configs())


def create_extra_permission(sender, **kwargs):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    global ALL_CONFIGS, COUNTER
    COUNTER += 1
    if COUNTER == ALL_CONFIGS:
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
                p, __ = Permission.objects.get_or_create(**params)



pre_migrate.connect(collect_apps, dispatch_uid='adminactions.collect_apps')
post_migrate.connect(create_extra_permission,
                     dispatch_uid='adminactions.create_extra_permission')
