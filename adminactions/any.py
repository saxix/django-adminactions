import json
from django import forms
from django.contrib.admin import helpers
from django.forms.models import modelform_factory
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from adminactions.forms import GenericActionForm


class AnyForm(GenericActionForm):
    _number = forms.BooleanField(label='Number',
        help_text="Number of records to create")


def create_random_records(modeladmin, request, queryset):
    MForm = modelform_factory(modeladmin.model, form=AnyForm)
    initial = {}
    if 'apply' in request.POST:
        pass

    form = MForm(initial=initial)
    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media

    tpl = 'adminactions/any_model.html'
    ctx = {'adminform': adminForm,
           'form': form,
           'title': u"Create  random %s records" % force_unicode(modeladmin.opts.verbose_name_plural),
#           'grouped': grouped,
#           'fieldvalues': json.dumps(grouped, default=dthandler),
           'change': True,
           'is_popup': False,
           'save_as': False,
           'has_delete_permission': False,
           'has_add_permission': False,
           'has_change_permission': True,
           'opts': modeladmin.model._meta,
           'app_label': modeladmin.model._meta.app_label,
           'action': 'create_random_records',
           'media': mark_safe(media),
           'selection': queryset}

    return render_to_response(tpl, RequestContext(request, ctx))

create_random_records.short_description = "Create random records"
