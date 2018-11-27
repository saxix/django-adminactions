# -*- coding: utf-8 -*-
from __future__ import absolute_import

from datetime import datetime

from django import forms
from django.contrib import messages
from django.contrib.admin import helpers
from django.db import models
from django.forms import HiddenInput, TextInput
from django.forms.formsets import formset_factory
from django.forms.models import model_to_dict, modelform_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from . import api, compat as transaction
from .forms import GenericActionForm
from .models import get_permission_codename
from .utils import clone_instance


class MergeForm(GenericActionForm):
    use_required_attribute = False

    DEP_MOVE = 1
    DEP_DELETE = 2
    GEN_IGNORE = 1
    GEN_RELATED = 2
    GEN_DEEP = 3

    dependencies = forms.ChoiceField(label=_('Dependencies'),
                                     choices=((DEP_MOVE, _("Move")), (DEP_DELETE, _("Delete"))))

    # generic = forms.ChoiceField(label=_('Search GenericForeignKeys'),
    #                             help_text=_("Search for generic relation"),
    #                             choices=((GEN_IGNORE, _("No")),
    #                                      (GEN_RELATED, _("Only Related (look for Managers)")),
    #                                      (GEN_DEEP, _("Analyze Mode (very slow)"))))

    master_pk = forms.CharField(widget=HiddenInput)
    other_pk = forms.CharField(widget=HiddenInput)
    field_names = forms.CharField(required=False, widget=HiddenInput)

    def action_fields(self):
        for fieldname in ['dependencies', 'master_pk', 'other_pk', 'field_names']:
            bf = self[fieldname]
            yield HiddenInput().render(fieldname, bf.value())

    def clean_dependencies(self):
        return int(self.cleaned_data['dependencies'])

    def clean_field_names(self):
        if self.cleaned_data['field_names']:
            return self.cleaned_data['field_names'].split(',')
        else:
            return None

    def full_clean(self):
        super(MergeForm, self).full_clean()

    def clean(self):
        return super(MergeForm, self).clean()

    def is_valid(self):
        return super(MergeForm, self).is_valid()

    class Media:
        js = [
            'admin/js/vendor/jquery/jquery.js',
            'admin/js/jquery.init.js',
            'adminactions/js/merge.min.js',
        ]
        css = {'all': ['adminactions/css/adminactions.min.css']}


def merge(modeladmin, request, queryset):  # noqa
    """
    Merge two model instances. Move all foreign keys.

    """

    opts = modeladmin.model._meta
    perm = "{0}.{1}".format(opts.app_label, get_permission_codename('adminactions_merge', opts))
    if not request.user.has_perm(perm):
        messages.error(request, _('Sorry you do not have rights to execute this action'))
        return

    def raw_widget(field, **kwargs):
        """ force all fields as not required"""
        kwargs['widget'] = TextInput({'class': 'raw-value'})
        if isinstance(field, models.FileField):
            kwargs["form_class"] = forms.CharField

        return field.formfield(**kwargs)

    merge_form = getattr(modeladmin, 'merge_form', MergeForm)
    MForm = modelform_factory(modeladmin.model,
                              form=merge_form,
                              exclude=('pk',),
                              formfield_callback=raw_widget)
    OForm = modelform_factory(modeladmin.model,
                              exclude=('pk',),
                              formfield_callback=raw_widget)

    tpl = 'adminactions/merge.html'
    # transaction_supported = model_supports_transactions(modeladmin.model)
    ctx = {
        '_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
        'transaction_supported': 'Un',
        'select_across': request.POST.get('select_across') == '1',
        'action': request.POST.get('action'),
        'fields': [f for f in queryset.model._meta.fields if not f.primary_key and f.editable],
        'app_label': queryset.model._meta.app_label,
        'result': '',
        'opts': queryset.model._meta}

    if 'preview' in request.POST:
        master = queryset.get(pk=request.POST.get('master_pk'))
        original = clone_instance(master)
        other = queryset.get(pk=request.POST.get('other_pk'))
        formset = formset_factory(OForm)(initial=[model_to_dict(master), model_to_dict(other)])
        with transaction.nocommit():
            form = MForm(request.POST, instance=master)
            other.delete()
            form_is_valid = form.is_valid()
        if form_is_valid:
            ctx.update({'original': original})
            tpl = 'adminactions/merge_preview.html'
        else:
            master = queryset.get(pk=request.POST.get('master_pk'))
            other = queryset.get(pk=request.POST.get('other_pk'))

    elif 'apply' in request.POST:
        master = queryset.get(pk=request.POST.get('master_pk'))
        other = queryset.get(pk=request.POST.get('other_pk'))
        formset = formset_factory(OForm)(initial=[model_to_dict(master), model_to_dict(other)])
        with transaction.nocommit():
            form = MForm(request.POST, instance=master)
            stored_pk = other.pk
            other.delete()
            ok = form.is_valid()
            other.pk = stored_pk
        if ok:
            if form.cleaned_data['dependencies'] == MergeForm.DEP_MOVE:
                related = api.ALL_FIELDS
                m2m = api.ALL_FIELDS
            else:
                related = None
                m2m = None
            fields = form.cleaned_data['field_names']
            api.merge(master, other, fields=fields, commit=True, m2m=m2m, related=related)
            return HttpResponseRedirect(request.get_full_path())
        else:
            messages.error(request, form.errors)
    else:
        try:
            master, other = queryset.all()
            # django 1.4 need to remove the trailing milliseconds
            for field in master._meta.fields:
                if isinstance(field, models.DateTimeField):
                    for target in (master, other):
                        raw_value = getattr(target, field.name)
                        if raw_value:
                            fixed_value = datetime(
                                raw_value.year,
                                raw_value.month,
                                raw_value.day,
                                raw_value.hour,
                                raw_value.minute,
                                raw_value.second)
                            setattr(target, field.name, fixed_value)
        except ValueError:
            messages.error(request, _('Please select exactly 2 records'))
            return

        initial = {'_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
                   'select_across': 0,
                   'generic': MergeForm.GEN_IGNORE,
                   'dependencies': MergeForm.DEP_MOVE,
                   'action': 'merge',
                   'master_pk': master.pk,
                   'other_pk': other.pk}
        formset = formset_factory(OForm)(initial=[model_to_dict(master), model_to_dict(other)])
        form = MForm(initial=initial, instance=master)

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    ctx.update({'adminform': adminForm,
                'formset': formset,
                'media': mark_safe(media),
                'action_short_description': merge.short_description,
                'title': u"%s (%s)" % (
                    merge.short_description.capitalize(),
                    smart_text(modeladmin.opts.verbose_name_plural),
                ),
                'master': master,
                'other': other})
    ctx.update(modeladmin.admin_site.each_context(request))
    return render(request, tpl, context=ctx)


merge.short_description = _("Merge selected %(verbose_name_plural)s")
