import os
import sys
from django.conf import settings


def pytest_configure(config):
    here = os.path.dirname(__file__)
    sys.path.insert(0, os.path.join(here, 'demo'))

    if not settings.configured:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'demoproject.settings'

def runtests(args=None):
    import pytest

    if not args:
        args = []

    if not any(a for a in args[1:] if not a.startswith('-')):
        args.append('adminactions')

    sys.exit(pytest.main(args))


if __name__ == '__main__':
    runtests(sys.argv)
