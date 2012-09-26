# -*- coding: utf-8 -*-
'''
Created on 28/ott/2009

@author: sax
'''
from django.db.models.aggregates import Count
from django.db.models.fields.related import ForeignKey
from django.forms.fields import CharField, BooleanField, ChoiceField
from django.forms.forms import Form, DeclarativeFieldsMetaclass
from django.forms.widgets import HiddenInput, MultipleHiddenInput
from django.utils import simplejson as json
from django.contrib import messages
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.encoding import force_unicode
from django.contrib.admin import helpers


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


def graph_queryset(modeladmin, request, queryset):
    MForm = graph_form_factory(modeladmin.model)

    graph_type = table = data_labels = data = total = None
    if 'apply' in request.POST:
        form = MForm(request.POST)
        if form.is_valid():
            try:
                x = form.cleaned_data['axes_x']
                #            y = form.cleaned_data['axes_y']
                graph_type = form.cleaned_data['graph_type']
                field, model, direct, m2m = modeladmin.model._meta.get_field_by_name(x)
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
                        data_labels.append(force_unicode(dict(field.flatchoices).get(value, value), strings_only=True))
                else:
                    data_labels = [str(l) for l, v in cc]
                data = [v for l, v in cc]
                table = zip(data_labels, data)
            except Exception as e:
                messages.error(request, 'Unable to produce valid data: %s' % str(e))
    elif request.method == 'POST':
        total = queryset.all().count()
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
           'app_label': queryset.model._meta.app_label,

           'as_json': json.dumps(table),
           'graph_type': graph_type,
           }
    return render_to_response('adminactions/charts.html', RequestContext(request, ctx))

graph_queryset.short_description = "Graph selected records"
