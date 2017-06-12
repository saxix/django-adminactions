from __future__ import absolute_import, unicode_literals

import datetime
import json
import re

import six
from collections import OrderedDict as SortedDict, defaultdict

import django
from django import forms
from django.contrib import messages
from django.contrib.admin import helpers
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import fields as df
from django.forms import fields as ff
from django.forms.models import (InlineForeignKeyField,
                                 ModelMultipleChoiceField, construct_instance,
                                 modelform_factory, )
from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.template.context import RequestContext
from django.utils.encoding import smart_text
from django.utils.functional import curry
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from adminactions.compat import atomic

# from adminactions import compat
from .compat import get_field_by_name
from .exceptions import ActionInterrupted
from .forms import GenericActionForm
from .models import get_permission_codename
from .signals import adminaction_end, adminaction_requested, adminaction_start

if six.PY2:
    import string
elif six.PY3:
    string = str

DO_NOT_MASS_UPDATE = 'do_NOT_mass_UPDATE'

add = lambda arg, value: value + arg
sub = lambda arg, value: value - arg
add_percent = lambda arg, value: value + (value * arg / 100)
sub_percent = lambda arg, value: value - (value * arg / 100)
negate = lambda value: not value
trim = lambda arg, value: value.strip(arg)

change_domain = lambda arg, value: re.sub('@.*', arg, value)
change_protocol = lambda arg, value: re.sub('^[a-z]*://', "%s://" % arg, value)

disable_if_not_nullable = lambda field: field.null
disable_if_unique = lambda field: not field.unique


class OperationManager(object):
    """
    Operate like a dictionary where the key are django.form.Field classes
    and value are tuple of function, param_allowed, enabler, description

    function: callable that can accept one or two arguments
                :param arg is the value set in the MassUpdateForm
                :param value is the existing field's value of the record
                :return new value to store
    param_allowed: boolean that enable the MassUpdateForm argument:
    enabler: boolean or callable that receive the specific Model field as argument
            and should returns True/False to indicate the `function` can be used with this
            specific field. i.e. disable 'set null` if the field cannot be null, or disable `set` if
            the field is unique
    description: string description of the operator
    """

    COMMON = [('set', (None, True, disable_if_unique, "")),
              ('set null', (lambda old_value: None, False, disable_if_not_nullable, ""))]

    def __init__(self, _dict):
        self._dict = dict()
        for field_class, args in list(_dict.items()):
            self._dict[field_class] = SortedDict(self.COMMON + args)

    def get(self, field_class, d=None):
        return self._dict.get(field_class, SortedDict(self.COMMON))

    def get_for_field(self, field):
        """ returns valid functions for passed field
            :param field Field django Model Field
            :return list of (label, (__, param, enabler, help))
        """
        valid = SortedDict()
        operators = self.get(field.__class__)
        for label, (func, param, enabler, help) in list(operators.items()):
            if (callable(enabler) and enabler(field)) or enabler is True:
                valid[label] = (func, param, enabler, help)
        return valid

    def __getitem__(self, field_class):
        return self.get(field_class)


OPERATIONS = OperationManager({
    df.CharField: [('upper', (string.upper, False, True, "convert to uppercase")),
                   ('lower', (string.lower, False, True, "convert to lowercase")),
                   ('capitalize', (string.capitalize, False, True, "capitalize first character")),
                   # ('capwords', (string.capwords, False, True, "capitalize each word")),
                   # ('swapcase', (string.swapcase, False, True, "")),
                   ('trim', (string.strip, False, True, "leading and trailing whitespace"))],
    df.IntegerField: [('add percent', (add_percent, True, True, "add <arg> percent to existing value")),
                      ('sub percent', (sub_percent, True, True, "")),
                      ('sub', (sub_percent, True, True, "")),
                      ('add', (add, True, True, ""))],
    df.BooleanField: [('swap', (negate, False, True, ""))],
    df.NullBooleanField: [('swap', (negate, False, True, ""))],
    df.EmailField: [('change domain', (change_domain, True, True, "")),
                    ('upper', (string.upper, False, True, "convert to uppercase")),
                    ('lower', (string.lower, False, True, "convert to lowercase"))],
    df.URLField: [('change protocol', (change_protocol, True, True, ""))]
})


class MassUpdateForm(GenericActionForm):
    _no_sample_for = []
    _clean = forms.BooleanField(label='clean()',
                                required=False,
                                help_text="if checked calls obj.clean()")

    _validate = forms.BooleanField(label='Validate',
                                   help_text="if checked use obj.save() instead of manager.update()")

    # _unique_transaction = forms.BooleanField(label='Unique transaction',
    # required=False,
    # help_text="If checked create one transaction for the whole update. "
    #                                                    "If any record cannot be updated everything will be rolled-back")

    def __init__(self, *args, **kwargs):
        super(MassUpdateForm, self).__init__(*args, **kwargs)
        self._errors = None

    # def is_valid(self):
    #    return super(MassUpdateForm, self).is_valid()

    def _get_validation_exclusions(self):
        exclude = super(MassUpdateForm, self)._get_validation_exclusions()
        for name, field in list(self.fields.items()):
            function = self.data.get('func_id_%s' % name, False)
            if function:
                exclude.append(name)
        return exclude

    def _post_clean(self):
        # must be overriden to bypass instance.clean()
        if self.cleaned_data.get('_clean', False):
            opts = self._meta
            self.instance = construct_instance(self, self.instance, opts.fields, opts.exclude)
            exclude = self._get_validation_exclusions()
            for f_name, field in list(self.fields.items()):
                if isinstance(field, InlineForeignKeyField):
                    exclude.append(f_name)
                    # Clean the model instance's fields.
            try:
                self.instance.clean_fields(exclude=exclude)
            except ValidationError as e:
                self._update_errors(e.message_dict)

    def _clean_fields(self):
        for name, field in list(self.fields.items()):
            raw_value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
            try:
                if isinstance(field, ff.FileField):
                    initial = self.initial.get(name, field.initial)
                    value = field.clean(raw_value, initial)
                else:
                    enabler = 'chk_id_%s' % name
                    function = self.data.get('func_id_%s' % name, False)
                    if self.data.get(enabler, False):
                        # field_object, model, direct, m2m = self._meta.model._meta.get_field_by_name(name)
                        field_object, model, direct, m2m = get_field_by_name(self._meta.model, name)
                        value = field.clean(raw_value)
                        if function:
                            func, hasparm, __, __ = OPERATIONS.get_for_field(field_object)[function]
                            if func is None:
                                pass
                            elif hasparm:
                                value = curry(func, value)
                            else:
                                value = func

                        self.cleaned_data[name] = value
                    if hasattr(self, 'clean_%s' % name):
                        value = getattr(self, 'clean_%s' % name)()
                        self.cleaned_data[name] = value
            except ValidationError as e:
                self._errors[name] = self.error_class(e.messages)
                if name in self.cleaned_data:
                    del self.cleaned_data[name]

    def clean__validate(self):
        return bool(self.data.get('_validate', 0))

    # def clean__unique_transaction(self):
    #     return bool(self.data.get('_unique_transaction', 0))

    def clean__clean(self):
        return bool(self.data.get('_clean', 0))


def mass_update(modeladmin, request, queryset):  # noqa
    """
        mass update queryset
    """

    def not_required(field, **kwargs):
        """ force all fields as not required"""
        kwargs['required'] = False
        return field.formfield(**kwargs)

    def _doit():
        errors = {}
        updated = 0
        for record in queryset:
            for field_name, value_or_func in list(form.cleaned_data.items()):
                if callable(value_or_func):
                    old_value = getattr(record, field_name)
                    setattr(record, field_name, value_or_func(old_value))
                else:
                    setattr(record, field_name, value_or_func)
            if clean:
                record.clean()
            record.save()
            updated += 1
        if updated:
            messages.info(request, _("Updated %s records") % updated)

        if len(errors):
            messages.error(request, "%s records not updated due errors" % len(errors))
        adminaction_end.send(sender=modeladmin.model,
                             action='mass_update',
                             request=request,
                             queryset=queryset,
                             modeladmin=modeladmin,
                             form=form,
                             errors=errors,
                             updated=updated)

    opts = modeladmin.model._meta
    perm = "{0}.{1}".format(opts.app_label, get_permission_codename('adminactions_massupdate', opts))
    if not request.user.has_perm(perm):
        messages.error(request, _('Sorry you do not have rights to execute this action'))
        return

    try:
        adminaction_requested.send(sender=modeladmin.model,
                                   action='mass_update',
                                   request=request,
                                   queryset=queryset,
                                   modeladmin=modeladmin)
    except ActionInterrupted as e:
        messages.error(request, str(e))
        return

    # Allows to specified a custom mass update Form in the ModelAdmin
    mass_update_form = getattr(modeladmin, 'mass_update_form', MassUpdateForm)

    MForm = modelform_factory(modeladmin.model, form=mass_update_form,
                              exclude=('pk',),
                              formfield_callback=not_required)
    grouped = defaultdict(lambda: [])
    selected_fields = []
    initial = {'_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
               'select_across': request.POST.get('select_across') == '1',
               'action': 'mass_update'}

    if 'apply' in request.POST:
        form = MForm(request.POST)
        if form.is_valid():
            try:
                adminaction_start.send(sender=modeladmin.model,
                                       action='mass_update',
                                       request=request,
                                       queryset=queryset,
                                       modeladmin=modeladmin,
                                       form=form)
            except ActionInterrupted as e:
                messages.error(request, str(e))
                return HttpResponseRedirect(request.get_full_path())

            # need_transaction = form.cleaned_data.get('_unique_transaction', False)
            validate = form.cleaned_data.get('_validate', False)
            clean = form.cleaned_data.get('_clean', False)

            if validate:
                with atomic():
                    _doit()

            else:
                values = {}
                for field_name, value in list(form.cleaned_data.items()):
                    if isinstance(form.fields[field_name], ModelMultipleChoiceField):
                        messages.error(request, "Unable no mass update ManyToManyField without 'validate'")
                        return HttpResponseRedirect(request.get_full_path())
                    elif callable(value):
                        messages.error(request, "Unable no mass update using operators without 'validate'")
                        return HttpResponseRedirect(request.get_full_path())
                    elif field_name not in ['_selected_action', '_validate', 'select_across', 'action',
                                            '_unique_transaction', '_clean']:
                        values[field_name] = value
                queryset.update(**values)

            return HttpResponseRedirect(request.get_full_path())
    else:
        initial.update({'action': 'mass_update', '_validate': 1})
        # form = MForm(initial=initial)
        prefill_with = request.POST.get('prefill-with', None)
        prefill_instance = None
        try:
            # Gets the instance directly from the queryset for data security
            prefill_instance = queryset.get(pk=prefill_with)
        except ObjectDoesNotExist:
            pass

        form = MForm(initial=initial, instance=prefill_instance)

    for el in queryset.all()[:10]:
        for f in modeladmin.model._meta.fields:
            if f.name not in form._no_sample_for:
                if hasattr(f, 'flatchoices') and f.flatchoices:
                    grouped[f.name] = list(dict(getattr(f, 'flatchoices')).values())
                elif hasattr(f, 'choices') and f.choices:
                    grouped[f.name] = list(dict(getattr(f, 'choices')).values())
                elif isinstance(f, df.BooleanField):
                    grouped[f.name] = [True, False]
                else:
                    value = getattr(el, f.name)
                    if value is not None and value not in grouped[f.name]:
                        grouped[f.name].append(value)
                    initial[f.name] = initial.get(f.name, value)

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.date) else str(obj)
    tpl = 'adminactions/mass_update.html'
    ctx = {'adminform': adminForm,
           'form': form,
           'action_short_description': mass_update.short_description,
           'title': u"%s (%s)" % (
               mass_update.short_description.capitalize(),
               smart_text(modeladmin.opts.verbose_name_plural),
           ),
           'grouped': grouped,
           'fieldvalues': json.dumps(grouped, default=dthandler),
           'change': True,
           'selected_fields': selected_fields,
           'is_popup': False,
           'save_as': False,
           'has_delete_permission': False,
           'has_add_permission': False,
           'has_change_permission': True,
           'opts': modeladmin.model._meta,
           'app_label': modeladmin.model._meta.app_label,
           # 'action': 'mass_update',
           # 'select_across': request.POST.get('select_across')=='1',
           'media': mark_safe(media),
           'selection': queryset}
    ctx.update(modeladmin.admin_site.each_context(request))

    if django.VERSION[:2] > (1, 8):
        return render(request, tpl, context=ctx)
    else:
        return render_to_response(tpl, RequestContext(request, ctx))


mass_update.short_description = _("Mass update")
