import logging
from itertools import chain

from django.conf import settings
from django.contrib import messages
from django.contrib.admin import helpers
from django.core import serializers as ser
from django.db import router
from django.db.models import ForeignKey, ManyToManyField
from django.db.models.deletion import Collector
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .api import export_as_csv as _export_as_csv
from .api import export_as_xls as _export_as_xls
from .exceptions import ActionInterrupted
from .forms import CSVOptions, FixtureOptions, XLSOptions
from .perms import get_permission_codename
from .signals import adminaction_end, adminaction_requested, adminaction_start

logger = logging.getLogger(__name__)


def get_action(request):
    try:
        action_index = int(request.POST.get("index", 0))
    except ValueError:
        action_index = 0
    return request.POST.getlist("action")[action_index]


def base_export(
    modeladmin,
    request,
    queryset,
    title,
    impl,  # noqa
    name,
    action_short_description,
    template,
    form_class,
):
    """
    export a queryset to csv file
    """
    opts = modeladmin.model._meta
    perm = "{0}.{1}".format(opts.app_label, get_permission_codename(base_export.base_permission, opts))
    if not request.user.has_perm(perm):
        messages.error(request, _("Sorry you do not have rights to execute this action"))
        return

    try:
        adminaction_requested.send(
            sender=modeladmin.model,
            action=name,
            request=request,
            queryset=queryset,
            modeladmin=modeladmin,
        )
    except ActionInterrupted as e:
        messages.error(request, str(e))
        return
    if hasattr(modeladmin, "get_exportable_columns"):
        cols = modeladmin.get_exportable_columns(request, form_class)
    else:
        cols = [
            (f.name, f.verbose_name) for f in queryset.model._meta.fields + queryset.model._meta.many_to_many
        ]
    initial = {
        "_selected_action": request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
        "select_across": request.POST.get("select_across") == "1",
        "action": get_action(request),
        "columns": [x for x, v in cols],
    }
    if initial["action"] == "export_as_csv":
        initial.update(getattr(settings, "ADMINACTIONS_CSV_OPTIONS_DEFAULT", {}))

    if "apply" in request.POST:
        form = form_class(request.POST)
        form.fields["columns"].choices = cols
        if form.is_valid():
            try:
                adminaction_start.send(
                    sender=modeladmin.model,
                    action=name,
                    request=request,
                    queryset=queryset,
                    modeladmin=modeladmin,
                    form=form,
                )
            except ActionInterrupted as e:
                messages.error(request, str(e))
                return

            if hasattr(modeladmin, "get_%s_filename" % name):
                filename = modeladmin.get_export_as_csv_filename(request, queryset)
            else:
                filename = None
            try:
                response = impl(
                    queryset,
                    fields=form.cleaned_data["columns"],
                    header=form.cleaned_data.get("header", False),
                    filename=filename,
                    options=form.cleaned_data,
                    modeladmin=modeladmin,
                )
            except Exception as e:
                logger.exception(e)
                messages.error(request, "Error: (%s)" % str(e))
            else:
                adminaction_end.send(
                    sender=modeladmin.model,
                    action=name,
                    request=request,
                    queryset=queryset,
                    modeladmin=modeladmin,
                    form=form,
                )
                return response
    else:
        form = form_class(initial=initial)
        form.fields["columns"].choices = cols

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    # tpl = 'adminactions/export_csv.html'
    ctx = {
        "adminform": adminForm,
        "change": True,
        "action_short_description": action_short_description,
        "title": title,
        "is_popup": False,
        "save_as": False,
        "has_delete_permission": False,
        "has_add_permission": False,
        "has_change_permission": True,
        "queryset": queryset,
        "opts": queryset.model._meta,
        "app_label": queryset.model._meta.app_label,
        "media": mark_safe(media),
    }
    ctx.update(modeladmin.admin_site.each_context(request))
    return render(request, template, ctx)


base_export.base_permission = "adminactions_export"


def export_as_csv(modeladmin, request, queryset):
    if hasattr(modeladmin, "get_aa_export_form"):
        form_class = modeladmin.get_aa_export_form(request, "csv") or CSVOptions
    else:
        form_class = CSVOptions
    return base_export(
        modeladmin,
        request,
        queryset,
        impl=_export_as_csv,
        name="export_as_csv",
        action_short_description=export_as_csv.short_description,
        title="%s (%s)"
        % (
            export_as_csv.short_description.capitalize(),
            modeladmin.opts.verbose_name_plural,
        ),
        template="adminactions/export_csv.html",
        form_class=form_class,
    )


export_as_csv.short_description = _("Export as CSV")
export_as_csv.base_permission = "adminactions_export"


def export_as_xls(modeladmin, request, queryset):
    if hasattr(modeladmin, "get_aa_export_form"):
        form_class = modeladmin.get_aa_export_form(request, "xls") or XLSOptions
    else:
        form_class = XLSOptions
    return base_export(
        modeladmin,
        request,
        queryset,
        impl=_export_as_xls,
        name="export_as_xls",
        action_short_description=export_as_xls.short_description,
        title="%s (%s)"
        % (
            export_as_xls.short_description.capitalize(),
            modeladmin.opts.verbose_name_plural,
        ),
        template="adminactions/export_xls.html",
        form_class=form_class,
    )


export_as_xls.short_description = _("Export as XLS")
export_as_xls.base_permission = "adminactions_export"


class FlatCollector:
    def __init__(self, using):
        self._visited = []
        super().__init__()

    def collect(self, objs):
        self.data = objs
        self.models = set([o.__class__ for o in self.data])


class ForeignKeysCollector:
    def __init__(self, using):
        self._visited = []
        super().__init__()

    def _collect(self, objs):
        objects = []
        for obj in objs:
            if obj and obj not in self._visited:
                concrete_model = obj._meta.concrete_model
                obj = concrete_model.objects.get(pk=obj.pk)
                opts = obj._meta

                self._visited.append(obj)
                objects.append(obj)
                for field in chain(opts.fields, opts.local_many_to_many):
                    if isinstance(field, ManyToManyField):
                        target = getattr(obj, field.name).all()
                        objects.extend(self._collect(target))
                    elif isinstance(field, ForeignKey):
                        target = getattr(obj, field.name)
                        objects.extend(self._collect([target]))
        return objects

    def collect(self, objs):
        self._visited = []
        self.data = self._collect(objs)
        self.models = set([o.__class__ for o in self.data])

    def __str__(self):
        return mark_safe(self.data)


def _dump_qs(form, queryset, data, filename):
    fmt = form.cleaned_data.get("serializer")

    json = ser.get_serializer(fmt)()
    ret = json.serialize(
        data,
        use_natural_foreign_keys=form.cleaned_data.get("use_natural_fk", False),
        use_natural_primary_keys=form.cleaned_data.get("use_natural_pk", False),
        indent=form.cleaned_data.get("indent"),
    )

    response = HttpResponse(content_type="application/json")
    if not form.cleaned_data.get("on_screen", False):
        filename = filename or "%s.%s" % (
            queryset.model._meta.verbose_name_plural.lower().replace(" ", "_"),
            fmt,
        )
        response["Content-Disposition"] = ('attachment;filename="%s"' % filename).encode(
            "us-ascii", "replace"
        )
    response.content = ret
    return response


def export_as_fixture(modeladmin, request, queryset):
    initial = {
        "_selected_action": request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
        "select_across": request.POST.get("select_across") == "1",
        "action": get_action(request),
        "serializer": "json",
        "indent": 4,
    }
    opts = modeladmin.model._meta
    perm = "{0}.{1}".format(opts.app_label, get_permission_codename(export_as_fixture.base_permission, opts))
    if not request.user.has_perm(perm):
        messages.error(request, _("Sorry you do not have rights to execute this action"))
        return

    try:
        adminaction_requested.send(
            sender=modeladmin.model,
            action="export_as_fixture",
            request=request,
            queryset=queryset,
            modeladmin=modeladmin,
        )
    except ActionInterrupted as e:
        messages.error(request, str(e))
        return
    if hasattr(modeladmin, "get_aa_export_form"):
        form_class = modeladmin.get_aa_export_form(request, "fixture") or FixtureOptions
    else:
        form_class = FixtureOptions

    if "apply" in request.POST:
        form = form_class(request.POST)
        if form.is_valid():
            try:
                adminaction_start.send(
                    sender=modeladmin.model,
                    action="export_as_fixture",
                    request=request,
                    queryset=queryset,
                    modeladmin=modeladmin,
                    form=form,
                )
            except ActionInterrupted as e:
                messages.error(request, str(e))
                return
            try:
                _collector = (
                    ForeignKeysCollector if form.cleaned_data.get("add_foreign_keys") else FlatCollector
                )
                c = _collector(None)
                c.collect(queryset)
                adminaction_end.send(
                    sender=modeladmin.model,
                    action="export_as_fixture",
                    request=request,
                    queryset=queryset,
                    modeladmin=modeladmin,
                    form=form,
                )

                if hasattr(modeladmin, "get_export_as_fixture_filename"):
                    filename = modeladmin.get_export_as_fixture_filename(request, queryset)
                else:
                    filename = None
                return _dump_qs(form, queryset, c.data, filename)
            except AttributeError as e:
                messages.error(request, str(e))
                return HttpResponseRedirect(request.path)
    else:
        form = form_class(initial=initial)

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    tpl = "adminactions/export_fixture.html"
    ctx = {
        "adminform": adminForm,
        "change": True,
        "action_short_description": export_as_fixture.short_description,
        "title": "%s (%s)"
        % (
            export_as_fixture.short_description.capitalize(),
            modeladmin.opts.verbose_name_plural,
        ),
        "is_popup": False,
        "save_as": False,
        "has_delete_permission": False,
        "has_add_permission": False,
        "has_change_permission": True,
        "queryset": queryset,
        "opts": queryset.model._meta,
        "app_label": queryset.model._meta.app_label,
        "media": mark_safe(media),
    }
    ctx.update(modeladmin.admin_site.each_context(request))
    return render(request, tpl, ctx)


export_as_fixture.short_description = _("Export as fixture")
export_as_fixture.base_permission = "adminactions_export"


def export_delete_tree(modeladmin, request, queryset):  # noqa
    """
    Export as fixture selected queryset and all the records that belong to.
    That mean that dump what will be deleted if the queryset was deleted
    """
    opts = modeladmin.model._meta
    perm = "{0}.{1}".format(
        opts.app_label,
        get_permission_codename(export_delete_tree.base_permission, opts),
    )
    if not request.user.has_perm(perm):
        messages.error(request, _("Sorry you do not have rights to execute this action"))
        return
    try:
        adminaction_requested.send(
            sender=modeladmin.model,
            action="export_delete_tree",
            request=request,
            queryset=queryset,
            modeladmin=modeladmin,
        )
    except ActionInterrupted as e:
        messages.error(request, str(e))
        return

    initial = {
        "_selected_action": request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
        "select_across": request.POST.get("select_across") == "1",
        "action": get_action(request),
        "serializer": "json",
        "indent": 4,
    }

    if hasattr(modeladmin, "get_aa_export_form"):
        form_class = modeladmin.get_aa_export_form(request, "delete") or FixtureOptions
    else:
        form_class = FixtureOptions

    if "apply" in request.POST:
        form = form_class(request.POST)
        if form.is_valid():
            try:
                adminaction_start.send(
                    sender=modeladmin.model,
                    action="export_delete_tree",
                    request=request,
                    queryset=queryset,
                    modeladmin=modeladmin,
                    form=form,
                )
            except ActionInterrupted as e:
                messages.error(request, str(e))
                return
            try:
                collect_related = form.cleaned_data.get("add_foreign_keys")
                using = router.db_for_write(modeladmin.model)

                c = Collector(using)
                c.collect(queryset, collect_related=collect_related)
                data = []
                for model, instances in list(c.data.items()):
                    data.extend(instances)
                adminaction_end.send(
                    sender=modeladmin.model,
                    action="export_delete_tree",
                    request=request,
                    queryset=queryset,
                    modeladmin=modeladmin,
                    form=form,
                )
                if hasattr(modeladmin, "get_export_delete_tree_filename"):
                    filename = modeladmin.get_export_delete_tree_filename(request, queryset)
                else:
                    filename = None
                return _dump_qs(form, queryset, data, filename)
            except AttributeError as e:
                messages.error(request, str(e))
                return HttpResponseRedirect(request.path)
    else:
        form = form_class(initial=initial)

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    tpl = "adminactions/export_fixture.html"
    ctx = {
        "adminform": adminForm,
        "change": True,
        "action_short_description": export_delete_tree.short_description,
        "title": "%s (%s)"
        % (
            export_delete_tree.short_description.capitalize(),
            modeladmin.opts.verbose_name_plural,
        ),
        "is_popup": False,
        "save_as": False,
        "has_delete_permission": False,
        "has_add_permission": False,
        "has_change_permission": True,
        "queryset": queryset,
        "opts": queryset.model._meta,
        "app_label": queryset.model._meta.app_label,
        "media": mark_safe(media),
    }
    ctx.update(modeladmin.admin_site.each_context(request))
    return render(request, tpl, ctx)


export_delete_tree.short_description = _("Export delete tree")
export_delete_tree.base_permission = "adminactions_export"
