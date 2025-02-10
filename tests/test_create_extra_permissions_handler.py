from unittest import mock
from unittest.mock import Mock

import pytest
from django.apps import apps

from adminactions import consts
from adminactions.apps import Config
from adminactions.models import create_extra_permissions_handler


@pytest.mark.parametrize("value", [consts.AA_PERMISSION_CREATE_USE_SIGNAL, consts.AA_PERMISSION_CREATE_USE_APPCONFIG])
def test_post_migrate(value):
    with mock.patch("adminactions.config.AA_PERMISSION_HANDLER", value):
        create_extra_permissions_handler(Mock())


def test_app_config():
    with mock.patch("adminactions.config.AA_PERMISSION_HANDLER", consts.AA_PERMISSION_CREATE_USE_APPCONFIG):
        with mock.patch("adminactions.perms.create_extra_permissions") as m:
            apps.get_app_config('adminactions').ready()

        assert m.call_count == 1
