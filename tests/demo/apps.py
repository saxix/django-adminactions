from __future__ import annotations

from django.apps import AppConfig


class Config(AppConfig):
    name = "demo"
    default = True

    def ready(self) -> None:
        try:
            from .celery import app  # noqa
        except ImportError:
            pass
