from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.template import Library

from adminactions.utils import get_field_value, get_verbose_name

if TYPE_CHECKING:
    from django.db.models.base import Model
    from django.db.models.fields import Field
    from django.db.models.query import QuerySet

register = Library()


@register.filter()
def field_display(obj: Model, field: Field) -> Any:
    """
    returns the representation (value or ``get_FIELD_display()``) of  a field

    see `adminactions.utils.get_field_value`_
    """
    return get_field_value(obj, field)


@register.filter
def verbose_name(model_or_queryset: Model | QuerySet, field: Field) -> str:
    """
    templatetag wrapper to `adminactions.utils.get_verbose_name`_
    """
    return get_verbose_name(model_or_queryset, field)
