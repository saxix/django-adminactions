from django.contrib.admin.actions import delete_selected
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _

__author__ = 'sax'


def empty_table(modeladmin, request, queryset):
    if not modeladmin.has_delete_permission(request):
        raise PermissionDenied
    delete_selected(modeladmin, request, modeladmin.model.objects.all())
empty_table.short_description = _("Delete all records")


def add_record(modeladmin, request, queryset):
    if not modeladmin.has_add_permission(request):
        raise PermissionDenied
    return HttpResponseRedirect('add/')


add_record.short_description = _("Add")

