import datetime
from itertools import chain
from django.core.serializers import get_serializer_formats
from django.db.models import ManyToManyField, ForeignKey
from django.forms.widgets import SelectMultiple
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.contrib import messages
from django.http import HttpResponse
import csv
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe
from django.contrib.admin import helpers
from django.utils import formats
from django.utils import dateformat
from adminactions.utils import flatten


delimiters = ",;|:"
quotes = "'\"`"
escapechars = " \\"


class CSVOptions(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    header = forms.BooleanField(required=False)
    delimiter = forms.ChoiceField(choices=zip(delimiters, delimiters))
    quotechar = forms.ChoiceField(choices=zip(quotes, quotes))
    quoting = forms.ChoiceField(
        choices=((csv.QUOTE_ALL, 'All'),
                 (csv.QUOTE_MINIMAL, 'Minimal'),
                 (csv.QUOTE_NONE, 'None'),
                 (csv.QUOTE_NONNUMERIC, 'Non Numeric')))

    escapechar = forms.ChoiceField(choices=(('', ''), ('\\', '\\')), required=False)
    datetime_format = forms.CharField(initial=formats.get_format('DATETIME_FORMAT'))
    date_format = forms.CharField(initial=formats.get_format('DATE_FORMAT'))
    time_format = forms.CharField(initial=formats.get_format('TIME_FORMAT'))
    columns = forms.MultipleChoiceField(widget=SelectMultiple(attrs={'size': 20}))


def export_as_csv(modeladmin, request, queryset):
    """
        export a queryset to csv file
    """
    cols = [(f.name, f.verbose_name) for f in queryset.model._meta.fields]
    initial = {helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(helpers.ACTION_CHECKBOX_NAME), 'quotechar': '"',
               'columns': [x for x, v in cols], 'quoting': csv.QUOTE_ALL, 'delimiter': ';', 'escapechar': '\\', }

    if 'apply' in request.POST:
        form = CSVOptions(request.POST)
        form.fields['columns'].choices = cols
        if form.is_valid():
            filename = "%s.csv" % queryset.model._meta.verbose_name_plural.lower().replace(" ", "_")
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment;filename="%s"' % filename
            try:
                writer = csv.writer(response,
                                    escapechar=str(form.cleaned_data['escapechar']),
                                    delimiter=str(form.cleaned_data['delimiter']),
                                    quotechar=str(form.cleaned_data['quotechar']),
                                    quoting=int(form.cleaned_data['quoting']))
                if form.cleaned_data.get('header', False):
                    writer.writerow([f for f in form.cleaned_data['columns']])

                for obj in queryset:
                    row = []
                    for fieldname in form.cleaned_data['columns']:
                        if hasattr(obj, 'get_%s_display' % fieldname):
                            value = getattr(obj, 'get_%s_display' % fieldname)()
                        else:
                            value = getattr(obj, fieldname)
                        if isinstance(value, datetime.datetime):
                            value = dateformat.format(value, form.cleaned_data['datetime_format'])
                        elif isinstance(value, datetime.date):
                            value = dateformat.format(value, form.cleaned_data['date_format'])
                        elif isinstance(value, datetime.time):
                            value = dateformat.format(value, form.cleaned_data['time_format'])
                        row.append(smart_str(value))
                    writer.writerow(row)
            except Exception as e:
                messages.error(request, "Error: (%s)" % str(e))
            else:
                return response
    else:
        form = CSVOptions(initial=initial)
        form.fields['columns'].choices = cols

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    tpl = 'adminactions/export_csv.html'
    ctx = {'adminform': adminForm,
           'form': form,
           'change': True,
           'title': _('Export to CSV'),
           'is_popup': False,
           'save_as': False,
           'has_delete_permission': False,
           'has_add_permission': False,
           'has_change_permission': True,
           'queryset': queryset,
           'opts': queryset.model._meta,
           'app_label': queryset.model._meta.app_label,
           'action': 'export_as_csv',
           'media': mark_safe(media)}
    return render_to_response(tpl, RequestContext(request, ctx))

export_as_csv.short_description = "Export as CSV"



class Collector2(object):
    def __init__(self):
        self._visited = []
        super(Collector2, self).__init__()

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


class FixtureOptions(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    use_natural_key = forms.BooleanField(required=False)
    on_screen = forms.BooleanField(label='Dump on screen', required=False)

    indent = forms.IntegerField(required=True, max_value=10, min_value=0)
    serializer = forms.ChoiceField(choices=zip(get_serializer_formats(), get_serializer_formats()))


def export_as_fixture(modeladmin, request, queryset):
    initial = {helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(helpers.ACTION_CHECKBOX_NAME), 'serializer': 'json', 'indent': 4}

    from django.db.models.deletion import Collector


    c = Collector2()
    c.collect(queryset)

    if 'apply' in request.POST:
        form = FixtureOptions(request.POST)
        if form.is_valid():
            import django.core.serializers as ser
            fmt = form.cleaned_data.get('serializer')
            json = ser.get_serializer(fmt)()
            ret = json.serialize(c.data, use_natural_keys=form.cleaned_data.get('use_natural_key', False),
                                 indent=form.cleaned_data.get('indent'))

            response = HttpResponse(mimetype='text/plain')
            if not form.cleaned_data.get('on_screen', False):
                filename = "%s.%s" % (queryset.model._meta.verbose_name_plural.lower().replace(" ", "_"), fmt)
                response['Content-Disposition'] = 'attachment;filename="%s"' % filename
            response.content = ret
            return response

    else:
        form = FixtureOptions(initial=initial)

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    tpl = 'adminactions/export_fixture.html'
    ctx = {'adminform': adminForm,
           'change': True,
           'title': _('Export as Fixture'),
           'is_popup': False,
           'save_as': False,
           'has_delete_permission': False,
           'has_add_permission': False,
           'has_change_permission': True,
           'queryset': queryset,
           'opts': queryset.model._meta,
           'app_label': queryset.model._meta.app_label,
           'action': 'export_as_fixture',
           'media': mark_safe(media)}
    return render_to_response(tpl, RequestContext(request, ctx))

export_as_fixture.short_description = "Export as fixture"
