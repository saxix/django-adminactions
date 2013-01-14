# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.admin import helpers
from django import forms
from django.forms.models import modelform_factory
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from django.utils.translation import gettext as _
from adminactions.forms import GenericActionForm


#class MergeForm(GenericActionForm):
class MergeForm(forms.Form):
    DEP_MOVE = 1
    DEP_DELETE = 2
    GEN_IGNORE = 1
    GEN_RELATED = 2
    GEN_DEEP = 3

    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    select_across = forms.BooleanField(label='', required=False, initial=0,
                                       widget=forms.HiddenInput({'class': 'select-across'}))
    action = forms.CharField(label='', required=True, initial='', widget=forms.HiddenInput())

    dependencies = forms.ChoiceField(label=_('Dependencies'),
                                     choices=((DEP_MOVE, _("Move")), (DEP_DELETE, _("Delete"))))

    generic = forms.ChoiceField(label=_('Search GenericForeignKeys'),
                                help_text=_("Search for generic relation"),
                                choices=((GEN_IGNORE, _("No")),
                                         (GEN_RELATED, _("Only Related (look for Managers)")),
                                         (GEN_DEEP, _("Analyze Mode (very slow)"))))

    class Media:
        js = ['adminactions/js/merge.js']
        css = {'all': ['adminactions/css/adminactions.css']}


def merge_record(origin, other, mapping):
    for field, source in mapping.items():
        if source == 1:
            pass
        elif source == 2:
            new_value = getattr(other, field)
            setattr(origin, new_value)
        else:
            raise ValueError("%s is not a valid value" % source)
    other.delete()
    origin.save(force_update=True)


def merge(modeladmin, request, queryset):
    """
    Merge two model instances. Move all foreign keys.

    """
    try:
        master, other = queryset.all()
    except ValueError:
        messages.error(request, _('Please select exactly 2 records'))
        return

    # Allows to specified a custom Form in the ModelAdmin
    MForm = getattr(modeladmin, 'merge_form', MergeForm)

    if 'apply' in request.POST:
        form = MForm(request.POST)
        if form.is_valid():
            mapping = {}
            for f in queryset.model._meta.fields:
                mapping[f.name] = request.POST.get("map-%s" % f.name)
            raise Exception(mapping)
#            merge_record(master, other, mapping)

            return HttpResponse(request.POST)
    else:
        initial = {'_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
                   'action': 'merge'}

        form = MForm(initial=initial)

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media

    tpl = 'adminactions/merge.html'
    ctx = {'_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
           'select_across': request.POST.get('select_across') == '1',
           'action': request.POST.get('action'),
           'adminform': adminForm,
           'app_label': queryset.model._meta.app_label,
           'media': mark_safe(media),
           'opts': queryset.model._meta,
           'fields': queryset.model._meta.fields,
           'master': master,
           'other': other}
    return render_to_response(tpl, RequestContext(request, ctx))


merge.short_description = "Merge selected records   "

