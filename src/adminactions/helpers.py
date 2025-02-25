from typing import TYPE_CHECKING, Any

from django import forms
from django.contrib import messages
from django.core import serializers
from django.core.exceptions import ValidationError
from django.db.models.base import Model
from django.template.response import TemplateResponse

from .perms import get_permission_codename

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.contrib.admin.options import ModelAdmin
    from django.http.request import HttpRequest
    from django.http.response import HttpResponse


class ImportFixtureForm(forms.Form):
    fixture_file = forms.FileField(required=False)
    fixture_content = forms.CharField(widget=forms.Textarea, required=False)

    use_natural_foreign_keys = forms.BooleanField(required=False)
    use_natural_primary_keys = forms.BooleanField(required=False)

    def clean(self) -> None:
        if not (self.cleaned_data["fixture_file"] or self.cleaned_data["fixture_content"]):
            raise ValidationError("You must provide file or content")


def import_fixture(modeladmin: "ModelAdmin", request: "HttpRequest") -> "HttpResponse":
    context = modeladmin.get_common_context(request)
    if request.method == "POST":
        form = ImportFixtureForm(data=request.POST)
        if form.is_valid():
            use_natural_fk = form.cleaned_data["use_natural_foreign_keys"]
            use_natural_pk = form.cleaned_data["use_natural_primary_keys"]
            ser_fmt = "json"
            try:
                if form.cleaned_data["fixture_content"]:
                    fixture_data = form.cleaned_data["fixture_content"]
                else:
                    fixture_data = request.FILES["fixture_file"].read()

                ser_fmt = "json"
                objects = serializers.deserialize(
                    ser_fmt,
                    fixture_data,
                    use_natural_foreign_keys=use_natural_fk,
                    use_natural_primary_keys=use_natural_pk,
                )
                imported = 0
                for obj in objects:
                    obj.save()
                    imported += 1

                modeladmin.message_user(request, f"{imported} objects imported", messages.SUCCESS)
            except Exception as e:  # noqa: BLE001
                modeladmin.message_user(request, f"{e.__class__.__name__}: {e}", messages.ERROR)

    else:
        form = ImportFixtureForm()
    context["form"] = form
    context["action"] = "Import fixture"
    return TemplateResponse(request, "adminactions/helpers/import_fixture.html", context)


class AdminActionPermMixin:
    model: Model

    def _filter_actions_by_permissions(
        self,
        request: "HttpRequest",
        actions: "list[tuple[Callable[[Any], Any], Any]]",
    ) -> "list[tuple[Callable[[Any], Any], Any]]":
        opts = self.model._meta
        filtered_actions = []
        actions = super()._filter_actions_by_permissions(request, actions)  # type: ignore[attr-defined, misc]
        from .actions import actions as aa  # noqa: PLC0415

        for action in actions:
            if action[0] in aa:
                perm = f"{opts.app_label}.{get_permission_codename(action[0].base_permission, opts)}"
                if not request.user.has_perm(perm):
                    continue
            filtered_actions.append(action)
        return filtered_actions
