# -*- coding: utf-8 -*-
import django.dispatch

adminaction_requested = django.dispatch.Signal(
    providing_args=["action", "request", "queryset", "modeladmin"])

adminaction_start = django.dispatch.Signal(
    providing_args=["action", "request", "queryset", "modeladmin", "form"])

adminaction_end = django.dispatch.Signal(
    providing_args=["action", "request", "queryset", "modeladmin", "form",
                    "errors", "updated"])
