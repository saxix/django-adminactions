from django.contrib.auth.management import _get_permission_codename
from django.db.models import signals


def create_extra_permission(sender, **kwargs):
    from django.contrib.auth.models import Permission
    from django.db.models.loading import get_models
    from django.contrib.contenttypes.models import ContentType

    for model in get_models(sender):
        for action in ('adminactions_export', 'adminactions_massupdate'):
            opts = model._meta
            codename = _get_permission_codename(action, opts)
            label = u'Can %s %s (adminactions)' % (action.replace('adminactions_', ""), opts.verbose_name_raw)
            ct = ContentType.objects.get_for_model(model)
            Permission.objects.get_or_create(codename=codename, content_type=ct, defaults={'name': label[:50]})


signals.post_syncdb.connect(create_extra_permission)
