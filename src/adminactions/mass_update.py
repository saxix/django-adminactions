from __future__ import annotations

import logging
import operator
import re
from collections import OrderedDict as SortedDict
from collections import defaultdict
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, TypeAlias

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.admin import helpers
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files import File
from django.db.models import FileField, ForeignKey
from django.db.models import fields as df
from django.db.models.query import QuerySet
from django.db.transaction import atomic
from django.forms import fields as ff
from django.forms.models import (
    InlineForeignKeyField,
    ModelMultipleChoiceField,
    construct_instance,
    modelform_factory,
)
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import smart_str
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from . import config
from .compat import celery_present
from .exceptions import ActionInterruptedError, MassUpdateSkipRecordError
from .forms import GenericActionForm
from .perms import get_permission_codename
from .signals import adminaction_end, adminaction_requested, adminaction_start, mass_update_process
from .utils import curry, get_field_by_name

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.contrib.admin.options import ModelAdmin
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.db.models.base import Model
    from django.db.models.fields.reverse_related import ForeignObjectRel
    from django.http.request import HttpRequest
    from django.http.response import HttpResponse

    AnyField: TypeAlias = df.Field[Any, Any] | ForeignObjectRel | GenericForeignKey
    TTransformer = Callable[[Any], Any] | Callable[[Any, Any], Any]
    TOperation = tuple[TTransformer | None, bool, bool | Callable[[Any], bool], str]
    TOperations = list[tuple[str, TOperation]]
    TOperationConfig: TypeAlias = dict[type[AnyField], TOperations]


logger = logging.getLogger(__name__)

DO_NOT_MASS_UPDATE = "do_NOT_mass_UPDATE"

add = lambda arg, value: value + arg
sub = lambda arg, value: value - arg
add_percent = lambda arg, value: value + (value * arg / 100)
sub_percent = lambda arg, value: value - (value * arg / 100)
negate = operator.not_
trim = lambda arg, value: value.strip(arg)

change_domain = lambda arg, value: re.sub(r"@.*", arg, value)
change_protocol = lambda arg, value: re.sub(r"^[a-z]*://", f"{arg}://", value)

disable_if_not_nullable = lambda field: field.null
disable_if_unique = lambda field: not field.unique


class OperationManager:
    """
    Operate like a dictionary where the key are django.form.Field classes
    and value are tuple of function, param_allowed, enabler, description

    function: callable that can accept one or two arguments
                :param arg is the value set in the MassUpdateForm
                :param value is the existing field's value of the record
                :return new value to store
    param_allowed: boolean that enable the MassUpdateForm argument:
    enabler: boolean or callable that receive the specific Model field as argument
            and should returns True/False to indicate the `function` can be used with this
            specific field. i.e. disable 'set null` if the field cannot be null, or disable `set` if
            the field is unique
    description: string description of the operator
    """

    COMMON: ClassVar[list[tuple[str, Any]]] = [
        ("set", (None, True, disable_if_unique, "")),
        ("set null", (lambda old_value: None, False, disable_if_not_nullable, "")),  # noqa: ARG005
    ]

    def __init__(self, _dict: TOperationConfig) -> None:
        self._dict: dict[type[AnyField], dict[str, TOperation]] = defaultdict(dict)
        self.operations: dict[str, TTransformer | None] = {}
        self.register_operations(df.Field, self.COMMON)
        for field_class, args in _dict.items():
            self.register_operations(field_class, args)

    def register_operations(
        self,
        field_class: type[AnyField],
        operations: TOperations,
    ) -> None:
        for label, operation in operations:
            self._dict[field_class][label] = operation
            if operation:
                self.operations[label] = operation[0]

    def get_function(self, name: str) -> TTransformer | None:
        return self.operations.get(name, None)

    def get(self, field_class: type[AnyField]) -> dict[str, TOperation]:
        data: dict[str, TOperation] = SortedDict()
        # reversed to make the most specific overrule the more general ones
        for typ in reversed(field_class.__mro__):
            data |= self._dict.get(typ, ())
        return data

    def operation_enabled(self, field: "AnyField", operation: TOperation) -> bool:  # noqa: PLR6301
        if operation:
            enabler = operation[2]
            return enabler is True or (callable(enabler) and enabler(field))
        return False

    def get_for_field(self, field: "AnyField") -> dict[str, TOperation]:
        """returns valid functions for passed field
        :param field Field django Model Field
        :return list of (label, (__, param, enabler, help))
        """
        return SortedDict([
            (label, operation)
            for label, operation in self.get(field.__class__).items()
            if self.operation_enabled(field, operation)
        ])

    def __getitem__(self, field_class: type[AnyField]) -> dict[str, TOperation]:
        return self.get(field_class)


OPERATIONS = OperationManager({
    df.CharField: [
        ("upper", (str.upper, False, True, _("convert to uppercase"))),
        ("lower", (str.lower, False, True, _("convert to lowercase"))),
        (
            "capitalize",
            (str.capitalize, False, True, _("capitalize first character")),
        ),
        ("trim", (str.strip, False, True, _("leading and trailing whitespace"))),
    ],
    df.IntegerField: [
        (
            "add percent",
            (add_percent, True, True, _("add <arg> percent to existing value")),
        ),
        ("sub percent", (sub_percent, True, True, "")),
        ("sub", (sub_percent, True, True, "")),
        ("add", (add, True, True, "")),
    ],
    df.BooleanField: [("toggle", (negate, False, True, ""))],
    # df.NullBooleanField: [("toggle", (negate, False, True, ""))],
    df.EmailField: [
        ("change domain", (change_domain, True, True, "")),
        ("upper", (str.upper, False, True, _("convert to uppercase"))),
        ("lower", (str.lower, False, True, _("convert to lowercase"))),
    ],
    df.URLField: [("change protocol", (change_protocol, True, True, ""))],
})


class MassUpdateFormProtocol(Protocol):
    def fix_json(self) -> None: ...


class MassUpdateForm(GenericActionForm):
    _async = forms.BooleanField(
        label="Async",
        required=False,
        help_text=_("use Celery to run update in background"),
    )
    _clean = forms.BooleanField(label="Clean()", required=False, help_text=_("if checked calls obj.clean()"))

    _validate = forms.BooleanField(
        label="Validate",
        required=False,
        help_text=_("if checked use obj.save() instead of manager.update()"),
    )
    sort_fields = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._errors = None
        self.update_using_queryset_allowed = True
        if not celery_present:
            self.fields["_async"].widget = forms.HiddenInput()

        if self.sort_fields:
            self.fields = dict(sorted(self.fields.items(), key=lambda item: item[1].label or ""))

    def _get_validation_exclusions(self) -> list[str]:
        exclude = list(super()._get_validation_exclusions())
        for name, __ in list(self.fields.items()):
            function = self.data.get(f"func_id_{name}", False)
            if function:
                exclude.append(name)
        return exclude

    def _post_clean(self) -> None:
        # must be overriden to bypass instance.clean()
        if self.cleaned_data.get("_clean", False):
            opts = self._meta
            self.instance = construct_instance(self, self.instance, opts.fields, opts.exclude)
            exclude = self._get_validation_exclusions()
            for f_name, field in list(self.fields.items()):
                if isinstance(field, InlineForeignKeyField):
                    exclude.append(f_name)
                    # Clean the model instance's fields.
            try:
                self.instance.clean_fields(exclude=exclude)
            except ValidationError as e:
                self._update_errors(e.message_dict)

    def full_clean(self) -> None:
        super().full_clean()

        def _is_field_name(n: str) -> bool:
            return not (n.startswith(("chk_id_", "func_id_")))

        def _is_enabled(n: str) -> bool:
            return bool(self.cleaned_data[f"chk_id_{n}"])

        if not self.is_bound:  # Stop further processing.
            return
        for field_name, __ in list(self.cleaned_data.items()):
            if (
                _is_field_name(field_name)
                and isinstance(self.fields.get(field_name, ""), forms.FileField)
                and self.cleaned_data["_async"]
                and self.cleaned_data.get(field_name, None)
            ):
                self.add_error(field_name, _("Cannot use Async with FileField"))

        if not self.cleaned_data.get("_validate"):
            if not self.update_using_queryset_allowed:
                self.add_error(None, "Cannot use operators without 'validate'")
            else:
                for field_name, __ in list(self.cleaned_data.items()):
                    if (
                        _is_field_name(field_name)
                        and _is_enabled(field_name)
                        and isinstance(self.fields.get(field_name, ""), ModelMultipleChoiceField)
                    ):
                        self.add_error(
                            field_name,
                            _("Unable no mass update ManyToManyField without 'validate'"),
                        )

    def _clean_fields(self) -> None:
        self.update_using_queryset_allowed = True
        self._errors = {}
        for name, field in list(self.fields.items()):
            raw_value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
            try:
                value = raw_value
                initial = self.initial.get(name, field.initial)
                enabler = f"chk_id_{name}"
                apply = self.data.get(enabler, "") == "on"
                self.cleaned_data[enabler] = apply
                if isinstance(field, ff.FileField):
                    value = field.clean(raw_value, initial)
                else:
                    function = self.data.get(f"func_id_{name}", "")
                    self.cleaned_data[f"func_id_{name}"] = function
                    if apply:
                        field_object, __, __, __ = get_field_by_name(self._meta.model, name)
                        value = field.clean(raw_value)
                        if function:
                            func, hasparm, __, __ = OPERATIONS.get_for_field(field_object)[function]
                            self.update_using_queryset_allowed &= func is None
                            if func is None:
                                pass
                            elif hasparm:
                                value = curry(func, value)
                            else:
                                value = func
                if hasattr(self, f"clean_{name}"):
                    value = getattr(self, f"clean_{name}")()
                self.cleaned_data[name] = value
            except ValidationError as e:
                self._errors[name] = self.error_class(e.messages)
                if name in self.cleaned_data:
                    del self.cleaned_data[name]

    def clean__validate(self) -> bool:
        return bool(self.data.get("_validate", 0))

    def clean__async(self) -> bool:
        return bool(self.data.get("_async", 0))

    def clean__clean(self) -> bool:
        return bool(self.data.get("_clean", 0))

    @property
    def media(self) -> forms.Media:
        extra = "" if settings.DEBUG else ".min"
        return super().media + forms.Media(
            js=(
                f"admin/js/vendor/jquery/jquery{extra}.js",
                f"adminactions/js/massupdate{extra}.js",
            ),
            css={
                "screen": ("adminactions/css/massupdate.css",),
            },
        )

    def fix_json(self) -> None:
        for label, field in self.fields.items():
            if isinstance(field, forms.JSONField):
                field.disabled = label not in self.data


def mass_update_execute(  # noqa: C901
    queryset: QuerySet[Model],
    rules: dict[str, tuple[callable, Any]],
    validate: bool,
    clean: bool,
    user_pk: Any,
    request: HttpRequest | None = None,
) -> tuple[int, dict[str, Any]]:
    errors: dict[str, Any] = {}
    updated: int = 0
    opts = queryset.model._meta
    adminaction_start.send(sender=queryset.model, action="mass_update", request=request, queryset=queryset)
    try:  # noqa: PLR1702
        with atomic():
            if not validate:
                values = {field_name: value for field_name, (func_name, value) in rules.items()}
                queryset.update(**values)
            else:
                for record in queryset:
                    try:
                        mass_update_process.send(sender=queryset.model, record=record, request=request)
                        for field_name, (func_name, value) in rules.items():
                            field = queryset.model._meta.get_field(field_name)
                            if isinstance(field, FileField):
                                file_field = getattr(record, field_name)
                                file_field.save(value.name, File(value.file))
                            else:
                                func = OPERATIONS.get_function(func_name)
                                if callable(func):
                                    old_value = getattr(record, field_name)
                                    setattr(record, field_name, func(old_value))
                                else:
                                    changed_attr = getattr(record, field_name, None)
                                    if changed_attr.__class__.__name__ == "ManyRelatedManager":
                                        changed_attr.set(value)
                                    else:
                                        setattr(record, field_name, value)

                        if clean:
                            record.clean()
                        record.save()
                        updated += 1
                    except MassUpdateSkipRecordError:
                        pass
            adminaction_end.send(
                sender=queryset.model,
                action="mass_update",
                request=request,
                queryset=queryset,
            )
            if config.AA_ENABLE_LOG:
                from django.contrib.admin.models import CHANGE, LogEntry  # noqa: PLC0415

                ids = list(queryset.only("pk").values_list("pk", flat=True))
                LogEntry.objects.log_action(
                    user_id=user_pk,
                    content_type_id=None,
                    object_id=None,
                    object_repr=f"Mass Update {opts.model_name}",
                    action_flag=CHANGE,
                    change_message={"rules": str(rules), "records": ids},
                )
    except ActionInterruptedError:
        updated, errors = 0, {}

    return updated, errors


def mass_update(modeladmin: ModelAdmin, request: HttpRequest, queryset: QuerySet) -> str | HttpResponse | None:  # noqa: C901, PLR0915, PLR0912, PLR0914
    """
    mass update queryset
    """

    def not_required(field: df.Field, **kwargs: Any) -> forms.Field:
        """force all fields as not required"""
        kwargs["required"] = False
        kwargs["request"] = request
        return modeladmin.formfield_for_dbfield(field, **kwargs)

    def _get_sample() -> dict[str, list[tuple[Any, str] | dict[str, Any]]]:
        grouped = defaultdict(list)
        for fname in mass_update_hints:
            f = modeladmin.model._meta.get_field(fname)
            if isinstance(f, ForeignKey):
                # Filter by queryset so we only get results without our
                # current resultset
                filters = {f"{f.remote_field.name}__in": queryset}
                # Order by random to get a nice sample
                query = f.related_model.objects.filter(**filters).distinct().order_by("?")
                # Limit the amount of results so we don't accidently query
                # many thousands of items and kill the database.
                grouped[f.name] = [(a.pk, str(a)) for a in query[:10]]
            elif hasattr(f, "flatchoices") and f.flatchoices:
                grouped[f.name] = dict(f.flatchoices).keys()
            elif hasattr(f, "choices") and f.choices:
                grouped[f.name] = dict(f.choices).keys()
            elif isinstance(f, df.BooleanField):
                grouped[f.name] = [("True", True), ("False", False)]
        already_grouped = set(grouped)
        for el in queryset.all()[:10]:
            for f in modeladmin.model._meta.fields:
                if f.name in mass_update_hints and f.name not in already_grouped:
                    value = getattr(el, f.name)
                    target = [str(value), value]
                    if value is not None and target not in grouped[f.name]:
                        grouped[f.name].append(target)

                    initial[f.name] = initial.get(f.name, value)
        return grouped

    opts = modeladmin.model._meta
    perm = ".".join([opts.app_label, get_permission_codename(mass_update.base_permission, opts)])
    if not request.user.has_perm(perm):
        messages.error(request, _("Sorry you do not have rights to execute this action"))
        return None
    if "apply" not in request.POST:
        try:
            adminaction_requested.send(
                sender=modeladmin.model,
                action="mass_update",
                request=request,
                queryset=queryset,
                modeladmin=modeladmin,
            )
        except ActionInterruptedError as e:
            messages.error(request, str(e))
            return None

    defaultFormClass = import_string(config.AA_MASSUPDATE_FORM)
    mass_update_form: type[MassUpdateForm] = getattr(modeladmin, "mass_update_form", defaultFormClass)
    mass_update_fields = getattr(modeladmin, "mass_update_fields", None)
    mass_update_exclude = getattr(modeladmin, "mass_update_exclude", None)
    if mass_update_fields and mass_update_exclude:
        raise ValueError("Cannot set both 'mass_update_exclude' and 'mass_update_fields'")

    if mass_update_exclude is None:
        mass_update_exclude = ["pk"]
    elif "pk" not in mass_update_exclude:
        mass_update_exclude.append("pk")
    mass_update_hints = getattr(modeladmin, "mass_update_hints", [])

    MForm = modelform_factory(
        modeladmin.model,
        form=mass_update_form,
        exclude=mass_update_exclude,
        fields=mass_update_fields,
        formfield_callback=not_required,
    )
    initial = {
        "_selected_action": request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
        "select_across": request.POST.get("select_across") == "1",
        "action": "mass_update",
    }
    rules = {}
    if "apply" in request.POST:
        try:
            form: MassUpdateForm = MForm(request.POST, request.FILES, initial=initial)
            if form.is_valid():
                validate = form.cleaned_data.get("_validate", False)
                clean = form.cleaned_data.get("_clean", False)
                use_celery = form.cleaned_data.get("_async", False)
                for field_name, v in list(form.cleaned_data.items()):
                    value = v
                    enabler = f"chk_id_{field_name}"
                    if form.data.get(enabler, False) == "on":
                        op = form.data.get(f"func_id_{field_name}")
                        if callable(value):
                            value = None
                        if isinstance(value, QuerySet):
                            rules[field_name] = (op, list(value.values_list("pk", flat=True)))
                        else:
                            rules[field_name] = (op, value)
                if use_celery:
                    from .tasks import mass_update_task  # noqa: PLC0415

                    mass_update_task.delay(
                        f"{opts.app_label}.{opts.model_name}",
                        ids=list(queryset.only("pk").values_list("pk", flat=True)),
                        rules=rules,
                        validate=validate,
                        clean=clean,
                        user_pk=request.user.pk,
                    )
                else:
                    try:
                        updated, __ = mass_update_execute(
                            queryset,
                            rules,
                            validate,
                            clean,
                            user_pk=request.user.pk,
                            request=request,
                        )
                        messages.info(request, _("Updated %s records") % updated)
                    except ActionInterruptedError as e:
                        messages.error(request, str(e))
                        return HttpResponseRedirect(request.get_full_path())
                return HttpResponseRedirect(request.get_full_path())

            form.fix_json()
        except Exception as e:
            messages.error(request, str(e))
            logger.exception(e)
            return HttpResponseRedirect(request.get_full_path())

    else:
        initial.update({"action": "mass_update", "_validate": 1})
        prefill_with = request.POST.get("prefill-with", None)
        try:
            # Gets the instance directly from the queryset for data security
            prefill_instance = queryset.get(pk=prefill_with)
        except ObjectDoesNotExist:
            prefill_instance = None

        form = MForm(initial=initial, instance=prefill_instance)

    sample_values = _get_sample() if mass_update_hints else None
    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    tpl = "adminactions/mass_update.html"
    ctx = {
        "adminform": adminForm,
        "form": form,
        "action_short_description": mass_update.short_description,  # type: ignore[attr-defined]
        "title": f"{mass_update.short_description.capitalize()} ({smart_str(modeladmin.opts.verbose_name_plural)})",  # type: ignore[attr-defined]
        "grouped": sample_values,
        "change": True,
        "rules": rules,
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


mass_update.short_description = _("Mass update")  # type: ignore[attr-defined]
mass_update.base_permission = "adminactions_massupdate"  # type: ignore[attr-defined]
