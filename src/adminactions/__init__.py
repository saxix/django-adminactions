import django_stubs_ext as django_stubs

from .version import __version__

VERSION = __version__

__all__ = ["VERSION", "__version__"]

django_stubs.monkeypatch()
