from django.contrib import messages
from django.contrib.admin import helpers
from django.forms.models import modelform_factory, modelformset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from .forms import GenericActionForm
from .perms import get_permission_codename
from .utils import get_ignored_fields


def byrows_update(modeladmin, request, queryset):  # noqa
    """
        by rows update queryset

        :type modeladmin: ModelAdmin
        :type request: HttpRequest
        :type queryset: QuerySet
    """

    opts = modeladmin.model._meta
    perm = "{0}.{1}".format(opts.app_label.lower(), get_permission_codename('adminactions_byrowsupdate', opts))
    if not request.user.has_perm(perm):
        messages.error(request, _('Sorry you do not have rights to execute this action'))
        return

    class modelform(modeladmin.form):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.instance:
                readonly_fields = (modeladmin.model._meta.pk.name,) + tuple(modeladmin.get_readonly_fields(request))
                for fname in readonly_fields:
                    if fname in self.fields:
                        self.fields[fname].widget.attrs['readonly'] = 'readonly'
                        self.fields[fname].widget.attrs['class'] = 'readonly'

    fields = byrows_update_get_fields(modeladmin)

    def formfield_callback(field, **kwargs):
        return modeladmin.formfield_for_dbfield(field, request=request, **kwargs)
    ActionForm = modelform_factory(
        modeladmin.model,
        form=GenericActionForm,
        fields=fields,
        formfield_callback=formfield_callback)

    MFormSet = modelformset_factory(modeladmin.model, form=modelform,
                                    fields=fields, extra=0,
                                    formfield_callback=formfield_callback)

    if 'apply' in request.POST:
        actionform = ActionForm(request.POST)
        formset = MFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            messages.info(request, _("Updated record(s)"))
            return HttpResponseRedirect(request.get_full_path())
    else:
        action_form_initial = {'_selected_action': request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
                               'select_across': request.POST.get('select_across') == '1',
                               'action': 'byrows_update'}
        actionform = ActionForm(initial=action_form_initial, instance=None)
        formset = MFormSet(queryset=queryset)

    adminform = helpers.AdminForm(
        actionform,
        modeladmin.get_fieldsets(request),
        {},
        [],
        model_admin=modeladmin)

    tpl = 'adminactions/byrows_update.html'
    ctx = {
        'adminform': adminform,
        'actionform': actionform,
        'action_short_description': byrows_update.short_description,
        'title': u"%s (%s)" % (
            byrows_update.short_description.capitalize(),
            smart_str(modeladmin.opts.verbose_name_plural),
        ),
        'formset': formset,
        'opts': modeladmin.model._meta,
        'app_label': modeladmin.model._meta.app_label,
    }
    ctx.update(modeladmin.admin_site.each_context(request))
    return render(request, tpl, ctx)


byrows_update.short_description = _("By rows update")


def byrows_update_get_fields(modeladmin):
    """
        Get fields names to be shown of the model rows formset considering the
        admin option:
        - adminactions_byrows_update_fields
        - adminactions_byrows_update_exclude
    """
    ignored_fields = get_ignored_fields(modeladmin.model, "UPDATE_ACTION_IGNORED_FIELDS")
    out = getattr(modeladmin, 'adminactions_byrows_update_fields',
                  [f.name for f in modeladmin.model._meta.fields if f.editable and f.name not in ignored_fields])
    if hasattr(modeladmin, 'adminactions_byrows_update_exclude'):
        fields = modeladmin.adminactions_byrows_update_exclude
        out = [fname for fname in fields if fname not in modeladmin.adminactions_byrows_update_exclude]
    return out
