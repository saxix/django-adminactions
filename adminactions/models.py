from django.contrib.auth.management import _get_permission_codename


def create_extra_permission(sender, **kwargs):
    from django.contrib.auth.models import Permission
    from django.db.models.loading import get_models
    from django.contrib.contenttypes.models import ContentType

    for model in get_models(sender):
        for action in ('export', 'massupdate', 'import'):
            opts = model._meta
            codename = _get_permission_codename(action, opts)
            label = u'Can %s %s' % (action, opts.verbose_name_raw)
            ct = ContentType.objects.get_for_model(model)
            Permission.objects.get_or_create(codename=codename, content_type=ct, defaults={'name': label})


