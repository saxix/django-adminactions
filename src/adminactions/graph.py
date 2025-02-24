import json
from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.admin import helpers
from django.db.models.aggregates import Count
from django.db.models.base import Model
from django.db.models.fields.related import ForeignKey
from django.forms.fields import BooleanField, CharField, ChoiceField
from django.forms.forms import DeclarativeFieldsMetaclass, Form
from django.forms.widgets import HiddenInput, MultipleHiddenInput
from django.shortcuts import render
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _

from .exceptions import ActionInterruptedError
from .perms import get_permission_codename
from .signals import adminaction_end, adminaction_requested, adminaction_start
from .utils import get_field_by_name

if TYPE_CHECKING:
    from http.client import HTTPResponse

    from django.contrib.admin import ModelAdmin
    from django.db.models import QuerySet
    from django.http.request import HttpRequest


def graph_form_factory(model: Model) -> Form:
    app_name = model._meta.app_label
    model_name = model.__name__

    model_fields = [(str(f.name), str(f.verbose_name)) for f in model._meta.fields if not f.primary_key]
    graphs = [("PieChart", "PieChart"), ("BarChart", "BarChart")]
    model_fields.insert(0, ("", "N/A"))
    class_name = f"{app_name}{model_name}GraphForm"
    attrs = {
        "initial": {"app": app_name, "model": model_name},
        "_selected_action": CharField(widget=MultipleHiddenInput),
        "select_across": BooleanField(initial="0", widget=HiddenInput, required=False),
        "app": CharField(initial=app_name, widget=HiddenInput),
        "model": CharField(initial=model_name, widget=HiddenInput),
        "graph_type": ChoiceField(label=_("Graph type"), choices=graphs, required=True),
        "axes_x": ChoiceField(label=_("Group by and count by"), choices=model_fields, required=True),
    }

    return DeclarativeFieldsMetaclass(str(class_name), (Form,), attrs)


def graph_queryset(modeladmin: "ModelAdmin", request: "HttpRequest", queryset: "QuerySet") -> "HTTPResponse":  # noqa: C901, PLR0912, PLR0914, PLR0915
    opts = modeladmin.model._meta
    perm = f"{opts.app_label.lower()}.{get_permission_codename(graph_queryset.base_permission, opts)}"
    if not request.user.has_perm(perm):
        messages.error(request, _("Sorry you do not have rights to execute this action"))
        return None

    MForm = graph_form_factory(modeladmin.model)

    graph_type = table = None
    extra = "{}"
    try:
        adminaction_requested.send(
            sender=modeladmin.model,
            action="graph_queryset",
            request=request,
            queryset=queryset,
            modeladmin=modeladmin,
        )
    except ActionInterruptedError as e:
        messages.error(request, str(e))
        return None

    if "apply" in request.POST:
        form = MForm(request.POST)
        if form.is_valid():
            try:
                adminaction_start.send(
                    sender=modeladmin.model,
                    action="graph_queryset",
                    request=request,
                    queryset=queryset,
                    modeladmin=modeladmin,
                    form=form,
                )
            except ActionInterruptedError as e:
                messages.error(request, str(e))
                return None
            try:
                x = form.cleaned_data["axes_x"]
                graph_type = form.cleaned_data["graph_type"]

                field, __, __, __ = get_field_by_name(modeladmin.model, x)
                cc = queryset.values_list(x).annotate(Count(x)).order_by()
                if isinstance(field, ForeignKey):
                    data_labels = []
                    for value, __ in cc:
                        data_labels.append(str(field.rel.to.objects.get(pk=value)))
                elif isinstance(field, BooleanField):
                    data_labels = [str(label) for label, v in cc]
                elif hasattr(modeladmin.model, f"get_{field.name}_display"):
                    data_labels = []
                    for value, __ in cc:
                        data_labels.append(smart_str(dict(field.flatchoices).get(value, value), strings_only=True))
                else:
                    data_labels = [str(label) for label, v in cc]
                data = [str(v) for label, v in cc]

                if graph_type == "BarChart":
                    table = [data]
                    extra = f"""{{seriesDefaults:{{renderer:$.jqplot.BarRenderer,
                                                rendererOptions: {{fillToZero: true,
                                                                  barDirection: 'horizontal'}},
                                                shadowAngle: -135,
                                               }},
                                series:[{json.dumps(data_labels)}],
                                axes: {{yaxis: {{renderer: $.jqplot.CategoryAxisRenderer,
                                                ticks: {json.dumps(data_labels)}}},
                                       xaxis: {{pad: 1.05,
                                               tickOptions: {{formatString: '%d'}}}}
                                      }}
                                }}"""
                else:  # graph_type == "PieChart":
                    table = [list(zip(list(map(str, data_labels)), list(map(str, data)), strict=True))]
                    extra = """{seriesDefaults: {renderer: jQuery.jqplot.PieRenderer,
                                                rendererOptions: {fill: true,
                                                                    showDataLabels: true,
                                                                    sliceMargin: 4,
                                                                    lineWidth: 5}},
                             legend: {show: true, location: 'e'}}"""

            except Exception as e:  # noqa: BLE001
                messages.error(request, f"Unable to produce valid data: {e!s}")
            else:
                adminaction_end.send(
                    sender=modeladmin.model,
                    action="graph_queryset",
                    request=request,
                    queryset=queryset,
                    modeladmin=modeladmin,
                    form=form,
                )
    else:  # if request.method == "POST":
        initial = {
            helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
            "select_across": request.POST.get("select_across", 0),
        }
        form = MForm(initial=initial)

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media

    ctx = {
        "adminform": adminForm,
        "action": "graph_queryset",
        "opts": modeladmin.model._meta,
        "action_short_description": graph_queryset.short_description,
        "title": f"{graph_queryset.short_description.capitalize()} ({smart_str(modeladmin.opts.verbose_name_plural)})",
        "app_label": queryset.model._meta.app_label,
        "media": media,
        "extra": extra,
        "as_json": json.dumps(table),
        "graph_type": graph_type,
    }
    ctx.update(modeladmin.admin_site.each_context(request))
    return render(request, "adminactions/charts.html", ctx)


graph_queryset.short_description = _("Graph selected records")
graph_queryset.base_permission = "adminactions_chart"
