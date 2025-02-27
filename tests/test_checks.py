from unittest import mock
from unittest.mock import Mock


def test_checks():
    from adminactions.checks import check_adminactions_settings
    errs = check_adminactions_settings(Mock())
    assert errs == []


def test_checks_error():
    from adminactions.checks import check_adminactions_settings
    with mock.patch('adminactions.config.AA_PERMISSION_HANDLER', "--"):
        errs = check_adminactions_settings(Mock())
        assert errs
