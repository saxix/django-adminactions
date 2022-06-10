from django.apps import AppConfig


class Config(AppConfig):
    name = "demo"
    default = True

    def ready(self):
        from .celery import app  # noqa
