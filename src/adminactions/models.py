from django.db.models.signals import post_migrate

import adminactions.perms as p


def create_extra_permissions_handler(sender, **kwargs):
    global TOTAL_MODELS, COUNTER
    if p.AA_PERMISSION_HANDLER == p.AA_PERMISSION_CREATE_USE_SIGNAL:
        p.create_extra_permissions()
    else:
        post_migrate.disconnect(dispatch_uid='adminactions.create_extra_permissions')


post_migrate.connect(create_extra_permissions_handler,
                     dispatch_uid='adminactions.create_extra_permissions')
