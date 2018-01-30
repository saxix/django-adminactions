# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.apps import apps
from django.db.models.signals import post_migrate


def get_permission_codename(action, opts):
    return '%s_%s' % (action, opts.object_name.lower())


# def get_models(a=None):
#     """Handles deprecation of django.db.models.loading in Django1.9"""
#
#     from django.apps import apps  # noqa
#     return apps.get_models()
#     # return [m for m in apps.get_models()]


def create_extra_permission(sender, **kwargs):
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
            p, __ = Permission.objects.get_or_create(**params)


post_migrate.connect(create_extra_permission)
