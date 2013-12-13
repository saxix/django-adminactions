# -*- coding: utf-8 -*-
from adminactions import api
from django.contrib import messages
from django.contrib.admin import helpers
from django import forms
from adminactions import transaction
from django.forms import TextInput, HiddenInput
from django.forms.formsets import formset_factory
from django.forms.models import modelform_factory, model_to_dict
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from adminactions.exceptions import FakeTransaction
from adminactions.forms import GenericActionForm
from adminactions.models import get_permission_codename
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
    field_names = forms.CharField(required=False)

    def action_fields(self):
        for fieldname in ['dependencies', 'master_pk', 'other_pk', 'field_names']:
            bf = self[fieldname]
            yield HiddenInput().render(fieldname, bf.value())

    def clean_dependencies(self):
        return int(self.cleaned_data['dependencies'])

    class Media:
        js = ['adminactions/js/merge.js']
        css = {'all': ['adminactions/css/adminactions.css']}


def merge(modeladmin, request, queryset):
    """
    Merge two model instances. Move all foreign keys.

    """

    opts = modeladmin.model._meta
    perm = "{0}.{1}".format(opts.app_label.lower(), get_permission_codename('adminactions_merge', opts))
    if not request.user.has_perm(perm):
        messages.error(request, _('Sorry you do not have rights to execute this action (%s)' % perm))
        return

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
        else:
            raise Exception(form.errors)
    elif 'apply' in request.POST:
        master = queryset.get(pk=request.POST.get('master_pk'))
        other = queryset.get(pk=request.POST.get('other_pk'))
        formset = formset_factory(OForm)(initial=[model_to_dict(master), model_to_dict(other)])
        with transaction.commit_manually():
            form = MForm(request.POST, instance=master)
            stored_pk = other.pk
            other.delete()
            ok = form.is_valid()
            transaction.rollback()
            other.pk = stored_pk
        if ok:
            if form.cleaned_data['dependencies'] == MergeForm.DEP_MOVE:
                related = api.ALL_FIELDS
            else:
                related = None
            fields = form.cleaned_data['field_names']
            api.merge(master, other, fields=fields, commit=True, related=related)
            return HttpResponseRedirect(request.path)
        else:
            messages.error(request, form.errors)

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


merge.short_description = _("Merge selected %(verbose_name_plural)s")
