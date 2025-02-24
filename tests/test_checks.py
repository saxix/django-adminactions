from unittest.mock import Mock


def test_checks():
    from adminactions.checks import check_adminactions_settings

    errs = check_adminactions_settings(Mock())
    assert errs == []
