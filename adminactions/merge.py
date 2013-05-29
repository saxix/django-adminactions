# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.admin import helpers
from django import forms
from django.db import transaction
from django.forms import TextInput, HiddenInput
from django.forms.formsets import formset_factory
from django.forms.models import modelform_factory, model_to_dict
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from adminactions.forms import GenericActionForm
from adminactions.utils import clone_instance


class MergeForm(GenericActionForm):
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

    def action_fields(self):
        for fieldname in ['dependencies', 'master_pk', 'other_pk']:
            bf = self[fieldname]
            yield HiddenInput().render(fieldname, bf.value())

    class Media:
        js = ['adminactions/js/merge.js']
        css = {'all': ['adminactions/css/adminactions.css']}


def merge(modeladmin, request, queryset):
    """
    Merge two model instances. Move all foreign keys.

    """

    def raw_widget(field, **kwargs):
        """ force all fields as not required"""
        kwargs['widget'] = TextInput({'class': 'raw-value', 'readonly': 'readonly'})
        kwargs['widget'] = TextInput({'class': 'raw-value', 'size': '30'})
        return field.formfield(**kwargs)

        # Allows to specified a custom Form in the ModelAdmin

    #    MForm = getattr(modeladmin, 'merge_form', MergeForm)
    merge_form = getattr(modeladmin, 'merge_form', MergeForm)
    MForm = modelform_factory(modeladmin.model, form=merge_form, formfield_callback=raw_widget)
    OForm = modelform_factory(modeladmin.model, formfield_callback=raw_widget)
    tpl = 'adminactions/merge.html'

    ctx = {
        '_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
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
        with transaction.commit_manually():
            form = MForm(request.POST, instance=master)
            other.delete()
            form_is_valid = form.is_valid()
            transaction.rollback()
        if form_is_valid:
            ctx.update({'original': original})
            tpl = 'adminactions/merge_preview.html'
    elif 'apply' in request.POST:
        master = queryset.get(pk=request.POST.get('master_pk'))
        other = queryset.get(pk=request.POST.get('other_pk'))
        formset = formset_factory(OForm)(initial=[model_to_dict(master), model_to_dict(other)])
        with transaction.commit_manually():
            form = MForm(request.POST, instance=master)
            other.delete()
            if form.is_valid():
                form.save()
                transaction.commit()
                return HttpResponseRedirect(request.path)
            else:
                messages.error(request, form.errors)
                transaction.rollback()
    else:
        try:
            master, other = queryset.all()
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
                'master': master,
                'other': other})
    return render_to_response(tpl, RequestContext(request, ctx))


merge.short_description = "Merge selected records"
