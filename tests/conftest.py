from __future__ import annotations

import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import pytest
from django_webtest import DjangoTestApp

if TYPE_CHECKING:

    class AppFactory(Protocol):
        def __call__(self, csrf_checks: bool, extra_environ: dict | None = None) -> DjangoTestApp: ...


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


def pytest_addoption(parser) -> None:
    group = parser.getgroup("selenium", "Selenium Web Browser Automation")
    group.addoption(
        "--selenium-enable",
        action="store_true",
        dest="selenium_enable",
        default=False,
        help="launch Selenium tests on hub",
    )

    group.addoption(
        "--chrome-driver",
        metavar="PATH",
        help="specify the full path for the chromedriver stored in your system. This is a mandatory field "
        "to let start Selenium tests even with Chrome. Command line sample: "
        "py.test --selenium-enable --chrome-driver=/home/chromedriver. -k test_name.",
    )

    parser.addoption(
        "--log",
        default=None,
        action="store",
        dest="log_level",
        help="enable console log",
    )

    parser.addoption(
        "--log-add",
        default="",
        action="store",
        dest="log_add",
        help="add package to log",
    )


def pytest_configure(config) -> None:
    here = Path(__file__).parent
    sys.path.insert(0, here)
    sys.path.insert(0, here.parent / "src")
    os.environ["DJANGO_SETTINGS_MODULE"] = "demo.settings"

    from django.conf import settings

    if (
        config.option.markexpr.find("selenium") < 0
        and not config.option.keyword
        and config.option.keyword.find("selenium") < 0
    ) and not config.option.selenium_enable:
        config.option.markexpr = "not selenium"
    os.environ["CELERY_ALWAYS_EAGER"] = "1"
    os.environ["MEDIA_ROOT"] = "/tmp/media/"
    settings.MEDIA_ROOT = tempfile.TemporaryDirectory().name
    original_media = os.path.join(settings.DEMO_DIR, "media")
    shutil.copytree(original_media, settings.MEDIA_ROOT)

    if config.option.log_level:
        import logging

        level = config.option.log_level.upper()
        assert level in levelNames
        format = "%(levelname)-7s %(name)-30s %(funcName)-20s:%(lineno)3s %(message)s"
        formatter = logging.Formatter(format)

        handler = logging.StreamHandler()
        handler.setLevel(levelNames[level])
        handler.setFormatter(formatter)

        for app in ["test", "demo", "adminactions"]:
            logger = logging.getLogger(app)
            logger.setLevel(levelNames[level])
            logger.addHandler(handler)

        if config.option.log_add:
            for pkg in config.option.log_add.split(","):
                logger = logging.getLogger(pkg)
                logger.setLevel(levelNames[level])
                logger.addHandler(handler)


@pytest.fixture(autouse=True)
def create_aa_permissions(db) -> None:
    from adminactions.perms import create_extra_permissions

    create_extra_permissions()


@pytest.fixture
def app(request, django_app_factory: "AppFactory") -> DjangoTestApp:
    return django_app_factory(csrf_checks=False)


@pytest.fixture
def users():
    from django.contrib.auth.models import User
    from django_dynamic_fixture import G

    return G(User, n=2, is_staff=False, is_active=False)


@pytest.fixture
def demomodels():
    from demo.models import DemoModel
    from django_dynamic_fixture import G

    return G(DemoModel, n=20)


@pytest.fixture
def admin():
    from django.contrib.auth.models import User
    from django_dynamic_fixture import G

    return G(User, is_staff=True, is_active=True)


@pytest.fixture
def administrator():
    from django.contrib.auth.models import User
    from utils import ADMIN, PWD

    return User._default_manager.create_superuser(username=ADMIN, password=PWD, email="sax@noreply.org")
