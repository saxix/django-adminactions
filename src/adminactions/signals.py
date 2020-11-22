import django.dispatch

adminaction_requested = django.dispatch.Signal()
adminaction_start = django.dispatch.Signal()
adminaction_end = django.dispatch.Signal()
