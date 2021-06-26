# -*- coding: utf-8 -*-

from django.apps import AppConfig


class Config(AppConfig):
    name = 'adminactions'

    def ready(self):
        from .models import create_extra_permission
        create_extra_permission(None)
