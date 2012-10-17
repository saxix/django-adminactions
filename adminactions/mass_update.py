import re
import json
import datetime
import string
from collections import defaultdict
from django import forms
from django.db import IntegrityError, transaction
from django.db.models import fields as df
from django.forms import fields as ff
from django.forms.models import modelform_factory, ModelMultipleChoiceField
from django.contrib import messages
from django.contrib.admin import helpers
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.encoding import force_unicode
from django.utils.functional import curry
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe

from adminactions.forms import GenericActionForm


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
        for field_class, args in _dict.items():
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
        for label, (func, param, enabler, help) in operators.items():
            if (callable(enabler) and enabler(field)) or enabler is True:
                valid[label] = (func, param, enabler, help)
        return valid

    def __getitem__(self, field_class):
        return self.get(field_class)


OPERATIONS = OperationManager({
    df.CharField: [('upper', (string.upper, False, True, "convert to uppercase")),
                   ('lower', (string.lower, False, True, "convert to lowercase")),
                   ('capitalize', (string.capitalize, False, True, "capitalize first character")),
                   ('capwords', (string.capwords, False, True, "capitalize each word")),
                   ('swapcase', (string.swapcase, False, True, "")),
                   ('trim', (string.strip, False, True, "leading and trailing whitespace"))],
    df.IntegerField: [('add percent', (add_percent, True, True, "add <arg> percent to existing value")),
                      ('sub percent', (sub_percent, True, True, "")),
                      ('sub', (sub_percent, True, True, "")),
                      ('add', (add, True, True, ""))],
    df.BooleanField: [('swap', (negate, False, True, ""))],
    df.NullBooleanField: [('swap', (negate, False, True, ""))],
    df.EmailField: [('change domain', (change_domain, True, True, ""))],
    df.URLField: [('change protocol', (change_protocol, True, True, ""))]
})


class MassUpdateForm(GenericActionForm):
    _validate = forms.BooleanField(label='Validate',
                                   help_text="if checked use obj.save() instead of manager.update()")
    _unique_transaction = forms.BooleanField(label='Unique transaction',
                                             help_text="if checked create one transaction for the whole update. "
                                                       "If some record canno be updated everything will be rolled-back")
    select_across = forms.BooleanField(label='', required=False, initial=0,
                                       widget=forms.HiddenInput({'class': 'select-across'}))
    action = forms.CharField(label='', required=True, initial='', widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(MassUpdateForm, self).__init__(*args, **kwargs)
        self._errors = None

    def _get_validation_exclusions(self):
        exclude = super(MassUpdateForm, self)._get_validation_exclusions()
        for name, field in self.fields.items():
            function = self.data.get('func_id_%s' % name, False)
            if function:
                exclude.append(name)
        return exclude

    def _clean_fields(self):
        for name, field in self.fields.items():
            raw_value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
            try:
                if isinstance(field, ff.FileField):
                    initial = self.initial.get(name, field.initial)
                    field.clean(value, initial)
                else:
                    enabler = 'chk_id_%s' % name
                    function = self.data.get('func_id_%s' % name, False)
                    if self.data.get(enabler, False):
                        field_object, model, direct, m2m = self._meta.model._meta.get_field_by_name(name)
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
            except ValidationError, e:
                self._errors[name] = self.error_class(e.messages)
                if name in self.cleaned_data:
                    del self.cleaned_data[name]

    def clean__validate(self):
        return bool(self.data.get('_validate', 0))

#    def clean(self):
#        return super(MassUpdateForm, self).clean()


def mass_update(modeladmin, request, queryset):
    """
        mass update queryset
    """
    def not_required(field, **kwargs):
        """ force all fields as not required"""
        kwargs['required'] = False
        return field.formfield(**kwargs)

    MForm = modelform_factory(modeladmin.model, form=MassUpdateForm, formfield_callback=not_required)
    grouped = defaultdict(lambda: [])
    selected_fields = []

    if 'apply' in request.POST:
        form = MForm(request.POST)
        if form.is_valid():

            need_transaction = form.cleaned_data.get('_unique_transaction', False)
            validate = form.cleaned_data.get('_validate', False)

            done = 0
            errors = 0
            if validate:
                if need_transaction:
                    transaction.enter_transaction_management()
                for record in queryset:
                    for field_name, value_or_func in form.cleaned_data.items():
                        if callable(value_or_func):
                            old_value = getattr(record, field_name)
                            setattr(record, field_name, value_or_func(old_value))
                        else:
                            setattr(record, field_name, value_or_func)
                    try:
                        record.clean()
                        record.save()
                    except IntegrityError as e:
                        errors += 1
                        if need_transaction:
                            transaction.rollback()
                            done = 0
                            break
                    else:
                        done += 1
                if done:
                    messages.info(request, "Updated %s records" % done)
                if errors:
                    messages.error(request, "%s records not updated due errors" % errors)
                if need_transaction:
                    transaction.commit()
            else:
                values = {}
                for field_name, value in form.cleaned_data.items():
                    if isinstance(form.fields[field_name], ModelMultipleChoiceField):
                        messages.error(request, "Unable no mass update ManyToManyField without 'validate'")
                        return HttpResponseRedirect(request.get_full_path())
                    elif callable(value):
                        messages.error(request, "Unable no mass update using operators without 'validate'")
                        return HttpResponseRedirect(request.get_full_path())
                    elif field_name not in ['_selected_action', '_validate', 'select_across', 'action']:
                        values[field_name] = value
                queryset.update(**values)
            return HttpResponseRedirect(request.get_full_path())
    else:

        initial = {'_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
                   'select_across': request.POST.get('select_across') == '1',
                   'action': 'mass_update',
                   '_validate': 1}
        form = MForm(initial=initial)

        for el in queryset.all()[:10]:
            for f in modeladmin.model._meta.fields:
                if hasattr(f, 'flatchoices') and f.flatchoices:
                    grouped[f.name] = dict(getattr(f, 'flatchoices')).values()
                elif hasattr(f, 'choices') and f.choices:
                    grouped[f.name] = dict(getattr(f, 'choices')).values()
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
           'title': u"Mass update %s" % force_unicode(modeladmin.opts.verbose_name_plural),
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
#           'action': 'mass_update',
#           'select_across': request.POST.get('select_across')=='1',
           'media': mark_safe(media),
           'selection': queryset}

    return render_to_response(tpl, RequestContext(request, ctx))

mass_update.short_description = "Mass update"
