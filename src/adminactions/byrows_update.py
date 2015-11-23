from django.shortcuts import render_to_response
from django.template.context import RequestContext

def byrows_update(modeladmin, request, queryset):  # noqa
    """
        by rows update queryset
    """

    tpl = 'adminactions/byrows_update.html'
    ctx = {
        'adminform': None,
        'opts': modeladmin.model._meta,
        'app_label': modeladmin.model._meta.app_label,
    }

    return render_to_response(tpl, RequestContext(request, ctx))

byrows_update.short_description = "By rows update"
