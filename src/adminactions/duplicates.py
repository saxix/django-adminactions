from django import forms
from django.contrib import messages
from django.contrib.admin import helpers
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.shortcuts import render
from django.utils.translation import gettext as _

from adminactions.exceptions import ActionInterrupted
from adminactions.perms import get_permission_codename
from adminactions.signals import adminaction_end, adminaction_requested, adminaction_start
from adminactions.utils import get_common_context


class DuplicatesForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    select_across = forms.BooleanField(
        label="",
        required=False,
        initial=0,
        widget=forms.HiddenInput({"class": "select-across"}),
    )
    action = forms.CharField(label="", required=True, initial="", widget=forms.HiddenInput())
    min = forms.IntegerField(required=True, initial=2)
    max = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop("model")
        self.field_names = []
        super().__init__(*args, **kwargs)
        for field in self.model._meta.concrete_fields:
            label = field.verbose_name
            if field.db_index:
                label = f"{label} **"
            self.field_names.append(field.name)
            self.fields[field.name] = forms.BooleanField(label=label, required=False)

    def clean(self):
        checked = [fname for fname in self.field_names if self.cleaned_data[fname]]
        if not checked:
            raise ValidationError("Select at least one field")
        return self.cleaned_data

    @property
    def media(self):
        return super().media + forms.Media(
            css={
                "screen": ("adminactions/css/adminactions.css",),
            },
        )


def find_duplicates(qs, fields, min_dupe=1, max_dupe=None):
    qs = qs.order_by()
    qs = qs.values(*fields)
    qs = qs.annotate(count_id=Count("id"))
    qs = qs.filter(count_id__gte=min_dupe)
    if max_dupe:
        qs = qs.filter(count_id__lte=max_dupe)
    return qs


def find_duplicates_action(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    perm = "{0}.{1}".format(
        opts.app_label,
        get_permission_codename(find_duplicates_action.base_permission, opts),
    )
    if not request.user.has_perm(perm):
        messages.error(request, _("Sorry you do not have rights to execute this action"))
        return
    ctx = get_common_context(
        modeladmin,
        action_short_description=find_duplicates_action.short_description,
        selection=queryset,
    )
    tpl = "adminactions/duplicates.html"
    initial = {
        "_selected_action": request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
        "select_across": request.POST.get("select_across") == "1",
        "action": "find_duplicates_action",
    }
    try:
        adminaction_requested.send(
            sender=modeladmin.model,
            action="find_duplicates_action",
            request=request,
            queryset=queryset,
            modeladmin=modeladmin,
        )
    except ActionInterrupted as e:
        messages.error(request, str(e))
        return
    if "apply" in request.POST:
        form = DuplicatesForm(request.POST, request.FILES, model=modeladmin.model)
        if form.is_valid():
            try:
                adminaction_start.send(
                    sender=queryset.model,
                    action="find_duplicates_action",
                    request=request,
                    queryset=queryset,
                    modeladmin=modeladmin,
                )
            except ActionInterrupted as e:
                messages.error(request, str(e))
                return

            min_dupe = form.cleaned_data["min"]
            max_dupe = form.cleaned_data.get("max", None)
            checked = [fname for fname in form.field_names if form.cleaned_data[fname]]
            qs = find_duplicates(
                modeladmin.get_queryset(request),
                checked,
                min_dupe=min_dupe,
                max_dupe=max_dupe,
            )
            ctx["results"] = qs.all()
            if not ctx["results"]:
                modeladmin.message_user(request, _("No duplicated rows found"), messages.WARNING)
            ctx["checked"] = checked
            ctx["sql"] = str(qs.query)
            adminaction_end.send(
                sender=queryset.model,
                action="find_duplicates_action",
                request=request,
                queryset=queryset,
            )
        else:
            pass
    else:
        form = DuplicatesForm(model=modeladmin.model, initial=initial)
    ctx["form"] = form
    return render(request, tpl, context=ctx)


find_duplicates_action.short_description = _("Find Duplicates")
find_duplicates_action.base_permission = "adminactions_find_duplicates"
