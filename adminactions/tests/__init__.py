from django.conf import settings
from .mass_update import *  # NOQA
from .exports import *  # NOQA
from .merge import MergeTest, MergeTestApi  # NOQA
from .export_api import * # NOQA

if getattr(settings, 'ENABLE_SELENIUM', True):
    try:
        import selenium  # NOQA
        from .selenium_tests import *  # NOQA
    except ImportError:
        import warnings

        warnings.warn('Unable load Selenium. Selenium tests will be disabled')
