# -*- coding: utf-8 -*-

from django.utils.translation import gettext as _
import django.dispatch


adminaction_requested = django.dispatch.Signal(providing_args=["action", "request", "queryset"])
adminaction_start = django.dispatch.Signal(providing_args=["action", "request", "queryset"])
adminaction_end = django.dispatch.Signal(providing_args=["action", "request", "queryset", "errors", "updated"])
