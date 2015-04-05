from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from django.conf import settings


def pytest_configure(config):
    try:
        from django.apps import AppConfig
        import django

        django.setup()
    except ImportError:
        pass
