from django.conf import settings

from .consts import AA_PERMISSION_CREATE_USE_SIGNAL

AA_PERMISSION_HANDLER = getattr(settings, 'AA_PERMISSION_HANDLER', AA_PERMISSION_CREATE_USE_SIGNAL)
AA_ENABLE_LOG = getattr(settings, 'AA_ENABLE_LOG', True)
