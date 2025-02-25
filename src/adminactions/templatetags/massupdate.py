from typing import TYPE_CHECKING, Any, TypeAlias

from django.db.models.base import Model
from django.forms import widgets
from django.template import Library
from django.template.context import Context
from django.utils.safestring import mark_safe

from adminactions.utils import get_field_by_name

if TYPE_CHECKING:
    from django.contrib.contenttypes.fields import GenericForeignKey
    from django.db.models import Field as DBField
    from django.db.models.fields.reverse_related import ForeignObjectRel

    AnyField: TypeAlias = DBField[Any, Any] | ForeignObjectRel | GenericForeignKey

register = Library()


@register.simple_tag
def fields_values(d: dict[str, list[str]], k: str) -> str:
    """
    >>> data = {
    ...     "name1": ["value1.1", "value1.2"],
    ...     "name2": ["value2.1", "value2.2"],
    ... }
    >>> print(fields_values(data, "name1"))
    value1.1,value1.2
    """
    values = d.get(k, [])
    return ",".join(map(str, values))


@register.simple_tag
def link_fields_values(d: dict[str, list[tuple[int, str]]], field_name: str) -> str:
    """
    >>> data = {'name1': [(1, 'value1.1'), (11, 'value1.2')],
    ...         'name2': [(2, 'value2.1'), (22, 'value2.2')], }
    >>> print(link_fields_values(data, 'name1'))
    <a name="name1_fastfieldvalue"><a href="#name1_fastfieldvalue" \
data-value="1" class="fastfieldvalue name1 value">value1.1</a>, \
<a name="name1_fastfieldvalue">\
<a href="#name1_fastfieldvalue" data-value="11" class="fastfieldvalue name1 value">value1.2</a>
    """
    ret = []
    name = f"{field_name}_fastfieldvalue"

    for el in d.get(field_name, []):
        try:
            value, label = el
        except (TypeError, ValueError):
            value, label = el, el

        if not label:  # ignore empty
            continue  # pragma: no cover
        ret.append(
            f'<a name="{name}"><a href="#{name}" data-value="{value}" '
            f'class="fastfieldvalue {field_name} value">{label}</a>',
        )

    return mark_safe(", ".join(ret))


@register.simple_tag(takes_context=True)
def checkbox_enabler(context: Context, field: "DBField[Any, Any]") -> str:
    form = context["adminform"].form
    name = f"chk_id_{field.name}"
    checked = ""
    if form.is_bound:
        chk = form.cleaned_data.get(name, False)
        checked = {True: 'checked="checked"', False: ""}[chk]
    return mark_safe(f'<input type="checkbox" name="{name}" {checked} class="enabler">')


@register.simple_tag(takes_context=True)
def field_function(context: Context, model: type[Model], field: "AnyField") -> str:
    from adminactions.mass_update import OPERATIONS  # noqa: PLC0415

    model_field, model, __, __ = get_field_by_name(model, field.name)
    attrs = {"class": "func_select"}
    options_attrs = {}
    choices = []
    classes = {True: "param", False: "noparam"}
    form = context["adminform"].form
    value = ""
    if form.is_bound:
        value = form.cleaned_data.get(f"func_id_{field.name}", "")

    for label, (__, param, __, __) in list(OPERATIONS.get_for_field(model_field).items()):
        options_attrs[label] = {"class": classes[param], "label": label}
        choices.append((label, label))
    return widgets.Select(attrs, choices).render(f"func_id_{field.name}", value)
