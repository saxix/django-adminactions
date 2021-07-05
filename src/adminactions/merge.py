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
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from . import api, compat as transaction
from .forms import GenericActionForm
from .perms import get_permission_codename
from .utils import clone_instance, get_ignored_fields


class MergeFormBase(forms.Form):
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
        super().full_clean()

    def clean(self):
        return super().clean()

    def is_valid(self):
        return super().is_valid()

    class Media:
        js = [
            'admin/js/vendor/jquery/jquery.js',
            'admin/js/jquery.init.js',
            'adminactions/js/merge.min.js',
        ]
        css = {'all': ['adminactions/css/adminactions.min.css']}


class MergeForm(GenericActionForm, MergeFormBase):
    pass


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

    def validate(request, master, other):
        """Validate the model is still valid after the merge"""
        merge_kwargs = {}
        with transaction.nocommit():
            merge_form = MergeFormBase(request.POST)
            if merge_form.is_valid():
                form = MForm(request.POST, instance=master)
                if merge_form.cleaned_data['dependencies'] == MergeForm.DEP_MOVE:
                    merge_kwargs['related'] = api.ALL_FIELDS
                    merge_kwargs['m2m'] = api.ALL_FIELDS
                else:
                    merge_kwargs['related'] = None
                    merge_kwargs['m2m'] = None
                merge_kwargs['fields'] = merge_form.cleaned_data['field_names']
                stored_pk = other.pk
                api.merge(master, other, commit=True, **merge_kwargs)
                other.pk = stored_pk
                return (form.is_valid(), form, merge_kwargs)
            else:
                return (False, merge_form, merge_kwargs)

    tpl = 'adminactions/merge.html'
    # transaction_supported = model_supports_transactions(modeladmin.model)
    ignored_fields = get_ignored_fields(queryset.model, "MERGE_ACTION_IGNORED_FIELDS")

    ctx = {
        '_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
        'transaction_supported': 'Un',
        'select_across': request.POST.get('select_across') == '1',
        'action': request.POST.get('action'),
        'fields': [f for f in queryset.model._meta.fields
                   if not f.primary_key and f.editable and f.name not in ignored_fields],
        'app_label': queryset.model._meta.app_label,
        'result': '',
        'opts': queryset.model._meta}
    if 'preview' in request.POST:
        master = queryset.get(pk=request.POST.get('master_pk'))
        original = clone_instance(master)
        other = queryset.get(pk=request.POST.get('other_pk'))
        formset = formset_factory(OForm)(initial=[model_to_dict(master), model_to_dict(other)])
        is_valid, form, merge_kwargs = validate(request, master, other)
        if is_valid:
            ctx.update({'original': original})
            tpl = 'adminactions/merge_preview.html'
        else:
            master = queryset.get(pk=request.POST.get('master_pk'))
            other = queryset.get(pk=request.POST.get('other_pk'))
            messages.error(request, form.errors)

    elif 'apply' in request.POST:
        master = queryset.get(pk=request.POST.get('master_pk'))
        other = queryset.get(pk=request.POST.get('other_pk'))
        formset = formset_factory(OForm)(initial=[model_to_dict(master), model_to_dict(other)])
        ok, form, merge_kwargs = validate(request, master, other)
        if ok:
            api.merge(master, other, commit=True, **merge_kwargs)
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
                    smart_str(modeladmin.opts.verbose_name_plural),
                ),
                'master': master,
                'other': other})
    ctx.update(modeladmin.admin_site.each_context(request))
    return render(request, tpl, context=ctx)


merge.short_description = _("Merge selected %(verbose_name_plural)s")
