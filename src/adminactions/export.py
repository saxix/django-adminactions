import logging
from collections.abc import Callable
from itertools import chain
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.contrib import messages
from django.contrib.admin import helpers
from django.core import serializers as ser
from django.db import router
from django.db.models import ForeignKey, ManyToManyField
from django.db.models.base import Model
from django.db.models.deletion import Collector
from django.db.models.query import QuerySet
from django.forms.forms import Form
from django.http import HttpResponse, HttpResponseRedirect
from django.http.request import HttpRequest
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .api import export_as_csv as _export_as_csv
from .api import export_as_xls as _export_as_xls
from .exceptions import ActionInterruptedError
from .forms import CSVOptions, FixtureOptions, XLSOptions
from .perms import get_permission_codename
from .signals import adminaction_end, adminaction_requested, adminaction_start

if TYPE_CHECKING:
    from collections.abc import Iterable

    from django.contrib.admin import ModelAdmin

logger = logging.getLogger(__name__)


def get_action(request: HttpRequest) -> str:
    try:
        action_index = int(request.POST.get("index", 0))
    except ValueError:
        action_index = 0
    return request.POST.getlist("action")[action_index]


def base_export(  # noqa: PLR0913, PLR0917
    modeladmin: "ModelAdmin[Model]",
    request: "HttpRequest",
    queryset: QuerySet[Model],
    title: str,
    impl: Callable[[QuerySet[Model], Any], HttpResponse],
    name: str,
    action_short_description: str,
    template: str,
    form_class: type[Form],
) -> HttpResponse | None:
    """
    export a queryset to csv file
    """
    opts = modeladmin.model._meta
    perm = f"{opts.app_label}.{get_permission_codename(base_export.base_permission, opts)}"
    if not request.user.has_perm(perm):
        messages.error(request, _("Sorry you do not have rights to execute this action"))
        return None

    try:
        adminaction_requested.send(
            sender=modeladmin.model,
            action=name,
            request=request,
            queryset=queryset,
            modeladmin=modeladmin,
        )
    except ActionInterruptedError as e:
        messages.error(request, str(e))
        return None
    if hasattr(modeladmin, "get_exportable_columns"):
        cols = modeladmin.get_exportable_columns(request, form_class)
    else:
        cols = [(f.name, f.verbose_name) for f in queryset.model._meta.fields + queryset.model._meta.many_to_many]
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
            except ActionInterruptedError as e:
                messages.error(request, str(e))
                return None

            filename = ff(request, queryset) if (ff := getattr(modeladmin, f"get_{name}_filename", None)) else None
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
                messages.error(request, f"Error: ({e!s})")
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


def export_as_csv(modeladmin: "ModelAdmin", request: HttpRequest, queryset: QuerySet) -> HttpResponse:
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
        title=f"{export_as_csv.short_description.capitalize()} ({modeladmin.opts.verbose_name_plural})",
        template="adminactions/export_csv.html",
        form_class=form_class,
    )


export_as_csv.short_description = _("Export as CSV")
export_as_csv.base_permission = "adminactions_export"


def export_as_xls(modeladmin: "ModelAdmin", request: HttpRequest, queryset: QuerySet) -> HttpResponse:
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
        title=f"{export_as_xls.short_description.capitalize()} ({modeladmin.opts.verbose_name_plural})",
        template="adminactions/export_xls.html",
        form_class=form_class,
    )


export_as_xls.short_description = _("Export as XLS")
export_as_xls.base_permission = "adminactions_export"


class FlatCollector:
    def __init__(self, using: str) -> None:  # noqa: ARG002
        self._visited = []
        super().__init__()

    def collect(self, objs: list[Model]) -> None:
        self.data = objs
        self.models = {o.__class__ for o in self.data}


class ForeignKeysCollector:
    def __init__(self, using: str) -> None:  # noqa: ARG002
        self._visited = []
        super().__init__()

    def _collect(self, objs: list[Model]) -> None:
        objects = []
        for o in objs:
            obj = o
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

    def collect(self, objs: list[Model]) -> None:
        self._visited = []
        self.data = self._collect(objs)
        self.models = {o.__class__ for o in self.data}

    def __str__(self) -> str:
        return mark_safe(self.data)


def _dump_qs(form: Form, queryset: QuerySet, data: "Iterable[Model]", filename: str) -> HttpResponse:
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
        filename = filename or "{}.{}".format(
            queryset.model._meta.verbose_name_plural.lower().replace(" ", "_"),
            fmt,
        )
        response["Content-Disposition"] = (f'attachment;filename="{filename}"').encode("us-ascii", "replace")
    response.content = ret
    return response


def export_as_fixture(
    modeladmin: "ModelAdmin", request: HttpRequest, queryset: QuerySet[Model]
) -> "HttpResponse | None":
    initial = {
        "_selected_action": request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
        "select_across": request.POST.get("select_across") == "1",
        "action": get_action(request),
        "serializer": "json",
        "indent": 4,
    }
    opts = modeladmin.model._meta
    perm = f"{opts.app_label}.{get_permission_codename(export_as_fixture.base_permission, opts)}"
    if not request.user.has_perm(perm):
        messages.error(request, _("Sorry you do not have rights to execute this action"))
        return None

    try:
        adminaction_requested.send(
            sender=modeladmin.model,
            action="export_as_fixture",
            request=request,
            queryset=queryset,
            modeladmin=modeladmin,
        )
    except ActionInterruptedError as e:
        messages.error(request, str(e))
        return None
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
            except ActionInterruptedError as e:
                messages.error(request, str(e))
                return None
            try:
                collector = ForeignKeysCollector if form.cleaned_data.get("add_foreign_keys") else FlatCollector
                c = collector(None)
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
        "title": f"{export_as_fixture.short_description.capitalize()} ({modeladmin.opts.verbose_name_plural})",
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


export_as_fixture.short_description = _("Export as fixture")  # type: ignore[attr-defined]
export_as_fixture.base_permission = "adminactions_export"  # type: ignore[attr-defined]


def export_delete_tree(
    modeladmin: "ModelAdmin[Model]", request: HttpRequest, queryset: QuerySet[Model]
) -> "HttpResponse | None":
    """
    Export as fixture selected queryset and all the records that belong to.
    That mean that dump what will be deleted if the queryset was deleted
    """
    opts = modeladmin.model._meta
    perm = f"{opts.app_label}.{get_permission_codename(export_delete_tree.base_permission, opts)}"  # type: ignore[attr-defined]
    if not request.user.has_perm(perm):
        messages.error(request, _("Sorry you do not have rights to execute this action"))
        return None
    try:
        adminaction_requested.send(
            sender=modeladmin.model,
            action="export_delete_tree",
            request=request,
            queryset=queryset,
            modeladmin=modeladmin,
        )
    except ActionInterruptedError as e:
        messages.error(request, str(e))
        return None

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
            except ActionInterruptedError as e:
                messages.error(request, str(e))
                return None
            try:
                collect_related = form.cleaned_data.get("add_foreign_keys")
                using = router.db_for_write(modeladmin.model)

                c = Collector(using)
                c.collect(queryset, collect_related=collect_related)
                data: list[Model] = []
                for __, instances in list(c.data.items()):
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
        "action_short_description": export_delete_tree.short_description,  # type: ignore[attr-defined]
        "title": f"{export_delete_tree.short_description.capitalize()} ({modeladmin.opts.verbose_name_plural})",  # type: ignore[attr-defined]
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


export_delete_tree.short_description = _("Export delete tree")  # type: ignore[attr-defined]
export_delete_tree.base_permission = "adminactions_export"  # type: ignore[attr-defined]
