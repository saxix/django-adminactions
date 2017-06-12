import logging

import django_webtest
import pytest

logger = logging.getLogger("test")

levelNames = {
    logging.CRITICAL: "CRITICAL",
    logging.ERROR: "ERROR",
    logging.WARNING: "WARNING",
    logging.INFO: "INFO",
    logging.DEBUG: "DEBUG",
    logging.NOTSET: "NOTSET",
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARN": logging.WARNING,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def pytest_addoption(parser):
    group = parser.getgroup("selenium", "Selenium Web Browser Automation")
    group.addoption(
        "--selenium-enable", action='store_true', dest='selenium_enable',
        default=False,
        help="launch Selenium tests on hub"
    )

    group.addoption(
        "--chrome-driver", metavar="PATH",
        help="specify the full path for the chromedriver stored in your system. This is a mandatory field "
             "to let start Selenium tests even with Chrome. Command line sample: "
             "py.test --selenium-enable --chrome-driver=/home/chromedriver. -k test_name."
    )

    parser.addoption("--log", default=None, action="store",
                     dest="log_level",
                     help="enable console log")

    parser.addoption("--log-add", default="", action="store",
                     dest="log_add",
                     help="add package to log")


def pytest_configure(config):
    # import warnings
    # enable this to removee deprecations
    # warnings.simplefilter('once', DeprecationWarning)

    if config.option.markexpr.find("selenium") < 0 and \
        not config.option.keyword and \
            config.option.keyword.find('selenium') < 0:
        if not config.option.selenium_enable:
            setattr(config.option, 'markexpr', 'not selenium')

    if config.option.log_level:
        import logging
        level = config.option.log_level.upper()
        assert level in levelNames.keys()
        format = "%(levelname)-7s %(name)-30s %(funcName)-20s:%(lineno)3s %(message)s"
        formatter = logging.Formatter(format)

        handler = logging.StreamHandler()
        handler.setLevel(levelNames[level])
        handler.setFormatter(formatter)

        for app in ["test", "demo", "adminactions"]:
            l = logging.getLogger(app)
            l.setLevel(levelNames[level])
            l.addHandler(handler)

        if config.option.log_add:
            for pkg in config.option.log_add.split(","):
                l = logging.getLogger(pkg)
                l.setLevel(levelNames[level])
                l.addHandler(handler)


@pytest.fixture(scope='function')
def app(request):
    wtm = django_webtest.WebTestMixin()
    wtm.csrf_checks = False
    wtm._patch_settings()
    request.addfinalizer(wtm._unpatch_settings)
    return django_webtest.DjangoTestApp()


@pytest.fixture(scope='function')
def users():
    from django.contrib.auth.models import User
    from django_dynamic_fixture import G

    return G(User, n=2, is_staff=False, is_active=False)


@pytest.fixture(scope='function')
def demomodels():
    from django_dynamic_fixture import G
    from demo.models import DemoModel

    return G(DemoModel, n=20)


@pytest.fixture(scope='function')
def admin():
    from django_dynamic_fixture import G
    from django.contrib.auth.models import User

    return G(User, is_staff=True, is_active=True)


@pytest.fixture(scope='function')
def administrator():
    from django.contrib.auth.models import User
    from utils import ADMIN, PWD

    superuser = User._default_manager.create_superuser(username=ADMIN,
                                                       password=PWD,
                                                       email="sax@noreply.org")
    return superuser
