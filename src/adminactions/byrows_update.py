from django.http import HttpRequest, HttpResponseRedirect
from django.db.models.query import QuerySet
from django.forms.models import modelform_factory
from django.contrib import messages
from django.contrib.admin import helpers, ModelAdmin
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from adminactions.forms import GenericActionForm
from django.forms import modelformset_factory
from django.utils.encoding import smart_text
from django.utils.translation import ugettext as _


def byrows_update(modeladmin, request, queryset):  # noqa
    """
        by rows update queryset

        :type modeladmin: ModelAdmin
        :type request: HttpRequest
        :type queryset: QuerySet
    """

    ActionForm = modelform_factory(modeladmin.model,
                    form = GenericActionForm,
                    exclude = ('id_geo',))

    MFormSet = modelformset_factory(modeladmin.model, exclude=('id_geo',), extra = 0)

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
        actionform = ActionForm(initial = action_form_initial, instance = None)
        formset = MFormSet(queryset = queryset)

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
        'title': u"By rows update %s" % smart_text(modeladmin.opts.verbose_name_plural),
        'formset': formset,
        'opts': modeladmin.model._meta,
        'app_label': modeladmin.model._meta.app_label,
    }

    return render_to_response(tpl, RequestContext(request, ctx))

byrows_update.short_description = "By rows update"
