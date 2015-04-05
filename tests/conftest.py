
def pytest_configure(config):
    try:
        from django.apps import AppConfig  # noqa
        import django

        django.setup()
    except ImportError:
        pass
