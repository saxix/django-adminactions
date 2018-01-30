
import json
from django.contrib import messages
from django.contrib.admin import helpers
from django.db.models.aggregates import Count
from django.db.models.fields.related import ForeignKey
from django.forms.fields import BooleanField, CharField, ChoiceField
from django.forms.forms import DeclarativeFieldsMetaclass, Form
from django.forms.widgets import HiddenInput, MultipleHiddenInput
from django.shortcuts import render
from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from .compat import get_field_by_name
from .exceptions import ActionInterrupted
from .models import get_permission_codename
from .signals import adminaction_end, adminaction_requested, adminaction_start


def graph_form_factory(model):
    app_name = model._meta.app_label
    model_name = model.__name__

    model_fields = [(f.name, f.verbose_name) for f in model._meta.fields if not f.primary_key]
    graphs = [('PieChart', 'PieChart'), ('BarChart', 'BarChart')]
    model_fields.insert(0, ('', 'N/A'))
    class_name = "%s%sGraphForm" % (app_name, model_name)
    attrs = {'initial': {'app': app_name, 'model': model_name},
             '_selected_action': CharField(widget=MultipleHiddenInput),
             'select_across': BooleanField(initial='0', widget=HiddenInput, required=False),
             'app': CharField(initial=app_name, widget=HiddenInput),
             'model': CharField(initial=model_name, widget=HiddenInput),
             'graph_type': ChoiceField(label="Graph type", choices=graphs, required=True),
             'axes_x': ChoiceField(label="Group by and count by", choices=model_fields, required=True)}

    return DeclarativeFieldsMetaclass(str(class_name), (Form,), attrs)


def graph_queryset(modeladmin, request, queryset):  # noqa
    opts = modeladmin.model._meta
    perm = "{0}.{1}".format(opts.app_label.lower(), get_permission_codename('adminactions_chart', opts))
    if not request.user.has_perm(perm):
        messages.error(request, _('Sorry you do not have rights to execute this action'))
        return

    MForm = graph_form_factory(modeladmin.model)

    graph_type = table = None
    extra = '{}'
    try:
        adminaction_requested.send(sender=modeladmin.model,
                                   action='graph_queryset',
                                   request=request,
                                   queryset=queryset,
                                   modeladmin=modeladmin)
    except ActionInterrupted as e:
        messages.error(request, str(e))
        return

    if 'apply' in request.POST:
        form = MForm(request.POST)
        if form.is_valid():
            try:
                adminaction_start.send(sender=modeladmin.model,
                                       action='graph_queryset',
                                       request=request,
                                       queryset=queryset,
                                       modeladmin=modeladmin,
                                       form=form)
            except ActionInterrupted as e:
                messages.error(request, str(e))
                return
            try:
                x = form.cleaned_data['axes_x']
                # y = form.cleaned_data['axes_y']
                graph_type = form.cleaned_data['graph_type']

                field, model, direct, m2m = get_field_by_name(modeladmin.model, x)
                cc = queryset.values_list(x).annotate(Count(x)).order_by()
                if isinstance(field, ForeignKey):
                    data_labels = []
                    for value, cnt in cc:
                        data_labels.append(str(field.rel.to.objects.get(pk=value)))
                elif isinstance(field, BooleanField):
                    data_labels = [str(l) for l, v in cc]
                elif hasattr(modeladmin.model, 'get_%s_display' % field.name):
                    data_labels = []
                    for value, cnt in cc:
                        data_labels.append(smart_text(dict(field.flatchoices).get(value, value), strings_only=True))
                else:
                    data_labels = [str(l) for l, v in cc]
                data = [v for l, v in cc]

                if graph_type == 'BarChart':
                    table = [data]
                    extra = """{seriesDefaults:{renderer:$.jqplot.BarRenderer,
                                                rendererOptions: {fillToZero: true,
                                                                  barDirection: 'horizontal'},
                                                shadowAngle: -135,
                                               },
                                series:[%s],
                                axes: {yaxis: {renderer: $.jqplot.CategoryAxisRenderer,
                                                ticks: %s},
                                       xaxis: {pad: 1.05,
                                               tickOptions: {formatString: '%%d'}}
                                      }
                                }""" % (json.dumps(data_labels), json.dumps(data_labels))
                elif graph_type == 'PieChart':
                    table = [list(zip(data_labels, data))]
                    extra = """{seriesDefaults: {renderer: jQuery.jqplot.PieRenderer,
                                                rendererOptions: {fill: true,
                                                                    showDataLabels: true,
                                                                    sliceMargin: 4,
                                                                    lineWidth: 5}},
                             legend: {show: true, location: 'e'}}"""

            except Exception as e:
                messages.error(request, 'Unable to produce valid data: %s' % str(e))
            else:
                adminaction_end.send(sender=modeladmin.model,
                                     action='graph_queryset',
                                     request=request,
                                     queryset=queryset,
                                     modeladmin=modeladmin,
                                     form=form)
    elif request.method == 'POST':
        # total = queryset.all().count()
        initial = {helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
                   'select_across': request.POST.get('select_across', 0)}
        form = MForm(initial=initial)
    else:
        initial = {helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
                   'select_across': request.POST.get('select_across', 0)}
        form = MForm(initial=initial)

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media

    ctx = {'adminform': adminForm,
           'action': 'graph_queryset',
           'opts': modeladmin.model._meta,
           'action_short_description': graph_queryset.short_description,
           'title': u"%s (%s)" % (
               graph_queryset.short_description.capitalize(),
               smart_text(modeladmin.opts.verbose_name_plural),
           ),
           'app_label': queryset.model._meta.app_label,
           'media': media,
           'extra': extra,
           'as_json': json.dumps(table),
           'graph_type': graph_type}
    ctx.update(modeladmin.admin_site.each_context(request))
    return render(request, 'adminactions/charts.html', ctx)


graph_queryset.short_description = _("Graph selected records")
