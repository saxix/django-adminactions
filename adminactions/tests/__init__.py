from __future__ import absolute_import
from django.conf import settings
from .test_mass_update import *  # NOQA
from .test_exports import *  # NOQA
from .test_merge import MergeTest, MergeTestApi  # NOQA
from .test_graph import TestGraph  # NOQA
from .test_api import TestExportAsCsv, TestExportAsExcel, TestExportQuerySetAsCsv, TestExportQuerySetAsExcel

import warnings
warnings.filterwarnings("ignore",
                                append=True,
                                category=DeprecationWarning,
                                message=".*AUTH_PROFILE_MODULE.*")


if getattr(settings, 'ENABLE_SELENIUM', True):
    try:
        import selenium  # NOQA
        from .selenium_tests import *  # NOQA
    except ImportError:
        import warnings

        warnings.warn('Unable load Selenium. Selenium tests will be disabled')


from adminactions.utils import get_field_value, get_field_by_path, get_verbose_name, flatten

__test__ = {
    'get_field_value': get_field_value,
    'get_field_by_path': get_field_by_path,
    'get_verbose_name': get_verbose_name,
    'flatten': flatten,


}
