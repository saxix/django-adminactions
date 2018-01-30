from itertools import chain

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.admin import helpers
from django.core import serializers as ser
from django.core.serializers import get_serializer_formats
from django.db import router
from django.db.models import ForeignKey, ManyToManyField
from django.db.models.deletion import Collector
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .api import (export_as_csv as _export_as_csv,
                  export_as_xls as _export_as_xls, )
from .exceptions import ActionInterrupted
from .forms import CSVOptions, XLSOptions
from .models import get_permission_codename
from .signals import adminaction_end, adminaction_requested, adminaction_start


def get_action(request):
    try:
        action_index = int(request.POST.get('index', 0))
    except ValueError:
        action_index = 0
    return request.POST.getlist('action')[action_index]


def base_export(modeladmin, request, queryset, title, impl,  # noqa
                name, action_short_description, template, form_class, ):
    """
        export a queryset to csv file
    """
    opts = modeladmin.model._meta
    perm = "{0}.{1}".format(opts.app_label, get_permission_codename('adminactions_export', opts))
    if not request.user.has_perm(perm):
        messages.error(request, _('Sorry you do not have rights to execute this action'))
        return

    try:
        adminaction_requested.send(sender=modeladmin.model,
                                   action=name,
                                   request=request,
                                   queryset=queryset,
                                   modeladmin=modeladmin)
    except ActionInterrupted as e:
        messages.error(request, str(e))
        return

    cols = [(f.name, f.verbose_name) for f in queryset.model._meta.fields +
            queryset.model._meta.many_to_many]
    initial = {'_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
               'select_across': request.POST.get('select_across') == '1',
               'action': get_action(request),
               'columns': [x for x, v in cols]}
    if initial["action"] == "export_as_csv":
        initial.update(getattr(
            settings, "ADMINACTIONS_CSV_OPTIONS_DEFAULT", {}))

    if 'apply' in request.POST:
        form = form_class(request.POST)
        form.fields['columns'].choices = cols
        if form.is_valid():
            try:
                adminaction_start.send(sender=modeladmin.model,
                                       action=name,
                                       request=request,
                                       queryset=queryset,
                                       modeladmin=modeladmin,
                                       form=form)
            except ActionInterrupted as e:
                messages.error(request, str(e))
                return

            if hasattr(modeladmin, 'get_%s_filename' % name):
                filename = modeladmin.get_export_as_csv_filename(request, queryset)
            else:
                filename = None
            try:
                response = impl(queryset,
                                fields=form.cleaned_data['columns'],
                                header=form.cleaned_data.get('header', False),
                                filename=filename,
                                options=form.cleaned_data)
            except Exception as e:
                messages.error(request, "Error: (%s)" % str(e))
            else:
                adminaction_end.send(sender=modeladmin.model,
                                     action=name,
                                     request=request,
                                     queryset=queryset,
                                     modeladmin=modeladmin,
                                     form=form)
                return response
    else:
        form = form_class(initial=initial)
        form.fields['columns'].choices = cols

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    # tpl = 'adminactions/export_csv.html'
    ctx = {'adminform': adminForm,
           'change': True,
           'action_short_description': action_short_description,
           'title': title,
           'is_popup': False,
           'save_as': False,
           'has_delete_permission': False,
           'has_add_permission': False,
           'has_change_permission': True,
           'queryset': queryset,
           'opts': queryset.model._meta,
           'app_label': queryset.model._meta.app_label,
           'media': mark_safe(media)}
    ctx.update(modeladmin.admin_site.each_context(request))
    return render(request, template, ctx)


def export_as_csv(modeladmin, request, queryset):
    return base_export(modeladmin, request, queryset,
                       impl=_export_as_csv,
                       name='export_as_csv',
                       action_short_description=export_as_csv.short_description,
                       title=u"%s (%s)" % (
                           export_as_csv.short_description.capitalize(),
                           modeladmin.opts.verbose_name_plural,
                       ),
                       template='adminactions/export_csv.html',
                       form_class=CSVOptions)


export_as_csv.short_description = _("Export as CSV")


def export_as_xls(modeladmin, request, queryset):
    return base_export(modeladmin, request, queryset,
                       impl=_export_as_xls,
                       name='export_as_xls',
                       action_short_description=export_as_xls.short_description,
                       title=u"%s (%s)" % (
                           export_as_xls.short_description.capitalize(),
                           modeladmin.opts.verbose_name_plural,
                       ),
                       template='adminactions/export_xls.html',
                       form_class=XLSOptions)


export_as_xls.short_description = _("Export as XLS")


class FlatCollector(object):
    def __init__(self, using):
        self._visited = []
        super(FlatCollector, self).__init__()

    def collect(self, objs):
        self.data = objs
        self.models = set([o.__class__ for o in self.data])


class ForeignKeysCollector(object):
    def __init__(self, using):
        self._visited = []
        super(ForeignKeysCollector, self).__init__()

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
    select_across = forms.BooleanField(label='', required=False, initial=0,
                                       widget=forms.HiddenInput({'class': 'select-across'}))
    action = forms.CharField(label='', required=True, initial='', widget=forms.HiddenInput())

    use_natural_key = forms.BooleanField(required=False)
    on_screen = forms.BooleanField(label='Dump on screen', required=False)
    add_foreign_keys = forms.BooleanField(required=False)

    indent = forms.IntegerField(required=True, max_value=10, min_value=0)
    serializer = forms.ChoiceField(choices=list(zip(get_serializer_formats(), get_serializer_formats())))


def _dump_qs(form, queryset, data, filename):
    fmt = form.cleaned_data.get('serializer')

    json = ser.get_serializer(fmt)()
    ret = json.serialize(data,
                         use_natural_foreign_keys=form.cleaned_data.get('use_natural_key', False),
                         indent=form.cleaned_data.get('indent'))

    response = HttpResponse(content_type='application/json')
    if not form.cleaned_data.get('on_screen', False):
        filename = filename or "%s.%s" % (queryset.model._meta.verbose_name_plural.lower().replace(" ", "_"), fmt)
        response['Content-Disposition'] = ('attachment;filename="%s"' % filename).encode('us-ascii', 'replace')
    response.content = ret
    return response


def export_as_fixture(modeladmin, request, queryset):
    initial = {'_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
               'select_across': request.POST.get('select_across') == '1',
               'action': get_action(request),

               'serializer': 'json',
               'indent': 4}
    opts = modeladmin.model._meta
    perm = "{0}.{1}".format(opts.app_label, get_permission_codename('adminactions_export', opts))
    if not request.user.has_perm(perm):
        messages.error(request, _('Sorry you do not have rights to execute this action'))
        return

    try:
        adminaction_requested.send(sender=modeladmin.model,
                                   action='export_as_fixture',
                                   request=request,
                                   queryset=queryset,
                                   modeladmin=modeladmin)
    except ActionInterrupted as e:
        messages.error(request, str(e))
        return

    if 'apply' in request.POST:
        form = FixtureOptions(request.POST)
        if form.is_valid():
            try:
                adminaction_start.send(sender=modeladmin.model,
                                       action='export_as_fixture',
                                       request=request,
                                       queryset=queryset,
                                       modeladmin=modeladmin,
                                       form=form)
            except ActionInterrupted as e:
                messages.error(request, str(e))
                return
            try:
                _collector = ForeignKeysCollector if form.cleaned_data.get('add_foreign_keys') else FlatCollector
                c = _collector(None)
                c.collect(queryset)
                adminaction_end.send(sender=modeladmin.model,
                                     action='export_as_fixture',
                                     request=request,
                                     queryset=queryset,
                                     modeladmin=modeladmin,
                                     form=form)

                if hasattr(modeladmin, 'get_export_as_fixture_filename'):
                    filename = modeladmin.get_export_as_fixture_filename(request, queryset)
                else:
                    filename = None
                return _dump_qs(form, queryset, c.data, filename)
            except AttributeError as e:
                messages.error(request, str(e))
                return HttpResponseRedirect(request.path)
    else:
        form = FixtureOptions(initial=initial)

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    tpl = 'adminactions/export_fixture.html'
    ctx = {'adminform': adminForm,
           'change': True,
           'action_short_description': export_as_fixture.short_description,
           'title': "%s (%s)" % (
               export_as_fixture.short_description.capitalize(),
               modeladmin.opts.verbose_name_plural,
           ),
           'is_popup': False,
           'save_as': False,
           'has_delete_permission': False,
           'has_add_permission': False,
           'has_change_permission': True,
           'queryset': queryset,
           'opts': queryset.model._meta,
           'app_label': queryset.model._meta.app_label,
           'media': mark_safe(media)}
    ctx.update(modeladmin.admin_site.each_context(request))
    return render(request, tpl, ctx)


export_as_fixture.short_description = _("Export as fixture")


def export_delete_tree(modeladmin, request, queryset):  # noqa
    """
    Export as fixture selected queryset and all the records that belong to.
    That mean that dump what will be deleted if the queryset was deleted
    """
    opts = modeladmin.model._meta
    perm = "{0}.{1}".format(opts.app_label, get_permission_codename('adminactions_export', opts))
    if not request.user.has_perm(perm):
        messages.error(request, _('Sorry you do not have rights to execute this action'))
        return
    try:
        adminaction_requested.send(sender=modeladmin.model,
                                   action='export_delete_tree',
                                   request=request,
                                   queryset=queryset,
                                   modeladmin=modeladmin)
    except ActionInterrupted as e:
        messages.error(request, str(e))
        return

    initial = {'_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
               'select_across': request.POST.get('select_across') == '1',
               'action': get_action(request),

               'serializer': 'json',
               'indent': 4}

    if 'apply' in request.POST:
        form = FixtureOptions(request.POST)
        if form.is_valid():
            try:
                adminaction_start.send(sender=modeladmin.model,
                                       action='export_delete_tree',
                                       request=request,
                                       queryset=queryset,
                                       modeladmin=modeladmin,
                                       form=form)
            except ActionInterrupted as e:
                messages.error(request, str(e))
                return
            try:
                collect_related = form.cleaned_data.get('add_foreign_keys')
                using = router.db_for_write(modeladmin.model)

                c = Collector(using)
                c.collect(queryset, collect_related=collect_related)
                data = []
                for model, instances in list(c.data.items()):
                    data.extend(instances)
                adminaction_end.send(sender=modeladmin.model,
                                     action='export_delete_tree',
                                     request=request,
                                     queryset=queryset,
                                     modeladmin=modeladmin,
                                     form=form)
                if hasattr(modeladmin, 'get_export_delete_tree_filename'):
                    filename = modeladmin.get_export_delete_tree_filename(request, queryset)
                else:
                    filename = None
                return _dump_qs(form, queryset, data, filename)
            except AttributeError as e:
                messages.error(request, str(e))
                return HttpResponseRedirect(request.path)
    else:
        form = FixtureOptions(initial=initial)

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    tpl = 'adminactions/export_fixture.html'
    ctx = {'adminform': adminForm,
           'change': True,
           'action_short_description': export_delete_tree.short_description,
           'title': u"%s (%s)" % (
               export_delete_tree.short_description.capitalize(),
               modeladmin.opts.verbose_name_plural,
           ),
           'is_popup': False,
           'save_as': False,
           'has_delete_permission': False,
           'has_add_permission': False,
           'has_change_permission': True,
           'queryset': queryset,
           'opts': queryset.model._meta,
           'app_label': queryset.model._meta.app_label,
           'media': mark_safe(media)}
    ctx.update(modeladmin.admin_site.each_context(request))
    return render(request, tpl, ctx)


export_delete_tree.short_description = _("Export delete tree")
