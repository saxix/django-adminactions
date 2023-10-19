import csv
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional, Sequence

from django import forms
from django.contrib import messages
from django.contrib.admin import helpers
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import FileExtensionValidator
from django.db.transaction import atomic
from django.forms import Media
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import smart_str
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from adminactions.exceptions import ActionInterrupted
from adminactions.forms import CSVConfigForm
from adminactions.perms import get_permission_codename
from adminactions.signals import (
    adminaction_end,
    adminaction_requested,
    adminaction_start,
)

logger = logging.getLogger(__name__)


class BulkUpdateForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    select_across = forms.BooleanField(
        label="",
        required=False,
        initial=0,
        widget=forms.HiddenInput({"class": "select-across"}),
    )
    action = forms.CharField(
        label="", required=True, initial="", widget=forms.HiddenInput()
    )

    _async = forms.BooleanField(
        label="Async",
        required=False,
        help_text=_("use Celery to run update in background"),
    )
    _clean = forms.BooleanField(
        label="Clean()", required=False, help_text=_("if checked calls obj.clean()")
    )

    _validate = forms.BooleanField(
        label="Validate",
        required=False,
        help_text=_("if checked use obj.save() instead of manager.bulk_update()"),
    )

    _date_format = forms.CharField(
        label="Date format", required=True, help_text=_("Date format")
    )
    _file = forms.FileField(
        label="CSV File",
        required=True,
        help_text=_("CSV file"),
        validators=[FileExtensionValidator(allowed_extensions=["csv", "txt"])],
    )

    @property
    def media(self):
        """Return all media required to render the widgets on this form."""
        media = Media(js=["adminactions/js/bulkupdate.js"])
        for field in self.fields.values():
            media = media + field.widget.media
        return media


class BulkUpdateMappingForm(forms.Form):
    index_field = forms.MultipleChoiceField(
        choices=[], widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop("model")
        super().__init__(*args, **kwargs)
        # self._errors = None
        # self.update_using_queryset_allowed = True
        for f in sorted(
            [
                (f.name, getattr(f, "verbose_name", f.name))
                for f in self.model._meta.get_fields()
            ],
            key=lambda item: item[1].casefold(),
        ):
            self.fields[f[0]] = forms.CharField(label=f[1].title(), required=False)
            # self.initial[f[0]] = f[0]
            # self.fields[f[0]].widget.initial = f[0]

    def _clean_fields(self):
        for name, field in self.fields.items():
            value = field.widget.value_from_datadict(
                self.data, self.files, self.add_prefix(name)
            )
            self.cleaned_data[name] = value
        if not self.cleaned_data["index_field"]:
            self.add_error(
                "index_field",
                ValidationError(_("Please select one or more index fields")),
            )

    def _post_clean(self):
        pass

    def get_mapping(self):
        mapping = self.cleaned_data.copy()
        mapping.pop("index_field")
        return {k: v for k, v in mapping.items() if v.strip()}


def bulk_update(modeladmin, request, queryset):  # noqa
    try:
        opts = modeladmin.model._meta
        perm = "{}.{}".format(
            opts.app_label, get_permission_codename(bulk_update.base_permission, opts)
        )
        bulk_update_form = getattr(modeladmin, "bulk_update_form", BulkUpdateForm)
        bulk_update_fields = getattr(modeladmin, "bulk_update_fields", None)
        bulk_update_exclude = getattr(modeladmin, "bulk_update_exclude", None)
        if bulk_update_exclude is None:
            bulk_update_exclude = []

        if bulk_update_fields and bulk_update_exclude:
            raise Exception(
                "Cannot set both 'bulk_update_exclude' and 'bulk_update_fields'"
            )
        if not request.user.has_perm(perm):
            messages.error(
                request, _("Sorry you do not have rights to execute this action")
            )
            return
        if "apply" not in request.POST:
            try:
                adminaction_requested.send(
                    sender=modeladmin.model,
                    action="bulk_update",
                    request=request,
                    queryset=queryset,
                    modeladmin=modeladmin,
                )
            except ActionInterrupted as e:
                messages.error(request, str(e))
                return
        form_initial = {
            "_selected_action": request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
            "_date_format": "%Y-%m-%d",
            "select_across": request.POST.get("select_across") == "1",
            "action": "bulk_update",
        }
        csv_initial = {
            "header": True,
            "quoting": csv.QUOTE_NONE,
            "escapechar": "",
            "quotechar": '"',
        }
        map_initial = {}
        if "apply" in request.POST:
            form = bulk_update_form(request.POST, request.FILES, initial=form_initial)
            csv_form = CSVConfigForm(request.POST, initial=csv_initial, prefix="csv")
            map_form = BulkUpdateMappingForm(
                request.POST, initial=map_initial, model=modeladmin.model, prefix="fld"
            )

            if form.is_valid() and csv_form.is_valid() and map_form.is_valid():
                header = csv_form.cleaned_data.pop("header")
                csv_options = csv_form.cleaned_data
                # validate = form.cleaned_data.get("_validate", False)
                clean = form.cleaned_data.get("_clean", False)
                # use_celery = form.cleaned_data.get("_async", False)
                try:
                    f = form.cleaned_data.pop("_file")
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                    temp_file.write(f.read())
                    temp_file.close()
                    res = _bulk_update(
                        queryset,
                        temp_file.name,
                        mapping=map_form.get_mapping(),
                        header=header,
                        clean=clean,
                        indexes=map_form.cleaned_data["index_field"],
                        csv_options=csv_options,
                    )
                    c = len(res["updated"])
                    messages.info(request, _("Updated %s records") % c)
                except ValueError as e:
                    messages.error(request, str(e))
                except ValidationError as e:
                    messages.error(request, str(e))
                    form.add_error(None, e)
                except ActionInterrupted as e:
                    messages.error(request, f"{e.__class__.__name__}: {e}")
                    return HttpResponseRedirect(request.get_full_path())
                except Exception as e:
                    messages.error(request, f"{e.__class__.__name__}: {e}")
                    return HttpResponseRedirect(request.get_full_path())
                else:
                    return HttpResponseRedirect(request.get_full_path())
                finally:
                    os.unlink(temp_file.name)
        else:
            form = bulk_update_form(initial=form_initial)
            csv_form = CSVConfigForm(initial=csv_initial, prefix="csv")
            map_form = BulkUpdateMappingForm(prefix="fld", model=modeladmin.model)

        adminForm = helpers.AdminForm(
            form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin
        )
        media = modeladmin.media + adminForm.media
        tpl = "adminactions/bulk_update.html"
        ctx = {
            "adminform": adminForm,
            "form": form,
            "csv_form": csv_form,
            "map_form": map_form,
            "action_short_description": bulk_update.short_description,
            "title": "%s (%s)"
            % (
                bulk_update.short_description.capitalize(),
                smart_str(modeladmin.opts.verbose_name_plural),
            ),
            "change": True,
            "is_popup": False,
            "save_as": False,
            "has_delete_permission": False,
            "has_add_permission": False,
            "has_change_permission": True,
            "opts": modeladmin.model._meta,
            "app_label": modeladmin.model._meta.app_label,
            "media": mark_safe(media),
            "selection": queryset,
        }
        ctx.update(modeladmin.admin_site.each_context(request))

        return render(request, tpl, context=ctx)
    except Exception as e:
        logger.exception(e)


bulk_update.short_description = _("Bulk update")
bulk_update.base_permission = "adminactions_bulkupdate"


def _bulk_update(  # noqa: max-complexity: 18
    queryset,
    filename,
    *,
    mapping: Dict,
    indexes: Sequence[str],
    clean=False,
    header: bool = True,
    csv_options: Optional[Dict] = None,
    request=None,
):
    results = {
        "updated": [],
        "errors": [],
        "missing": [],
        "duplicates": [],
    }
    adminaction_start.send(
        sender=queryset.model, action="bulk_update", request=request, queryset=queryset
    )
    try:
        with Path(filename).open("r") as f:
            if header:
                reader = csv.DictReader(
                    f.readlines(), skipinitialspace=True, **(csv_options or {})
                )
                for _k, v in mapping.items():
                    if v not in reader.fieldnames:
                        raise ValidationError(
                            _("%s column is not present in the file") % v
                        )
            else:
                reader = csv.reader(f.readlines(), **(csv_options or {}))
                mapping = {k: int(v) - 1 for k, v in mapping.items()}

            reverse = {v: k for k, v in mapping.items()}
            with atomic():
                for row in reader:
                    key = {k: row[mapping[k]] for k in indexes}
                    try:
                        obj = queryset.get(**key)
                        if header:
                            for colname, value in row.items():
                                field = reverse[colname]
                                if field not in indexes:
                                    model_field = queryset.model._meta.get_field(field)
                                    if (
                                        model_field.is_relation
                                        and model_field.many_to_one
                                    ):
                                        related_model = model_field.related_model
                                        try:
                                            value = related_model.objects.get(pk=value)
                                        except ObjectDoesNotExist:
                                            raise ValidationError(
                                                f"No {related_model._meta.verbose_name} found with id {value}"
                                            )
                                    setattr(obj, field, value)
                        else:
                            for i, value in enumerate(row):
                                if i in reverse.keys():
                                    field = reverse[i]
                                    if field not in indexes:
                                        setattr(obj, field, value)
                        if clean:
                            obj.clean()
                        obj.save()
                        results["updated"].append(key)
                    except queryset.model.DoesNotExist:
                        results["missing"].append(key)
                    except queryset.model.MultipleObjectsReturned:
                        results["duplicates"].append(key)
        adminaction_end.send(
            sender=queryset.model,
            action="bulk_update",
            request=request,
            queryset=queryset,
        )
    except ActionInterrupted:
        pass
    except Exception as e:
        logger.exception(e)
        raise
    return results
