import os

try:
    from celery import Celery
    from django.conf import settings

    # set the default Django settings module for the 'celery' program.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "demo.settings")
    app = Celery("demo")

    # Using a string here means the worker will not have to
    # pickle the object when using Windows.
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
    assert app.conf.task_always_eager
except ImportError:
    pass
