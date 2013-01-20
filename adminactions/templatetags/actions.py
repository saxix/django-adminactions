# -*- coding: utf-8 -*-
from django.template import Library
from adminactions.utils import get_field_value, get_verbose_name


register = Library()


@register.filter()
def raw_value(obj, field):
    """
        returns the value  a field

        see `adminactions.utils.get_field_value`_
    """
    value = get_field_value(obj, field, False)
    return str(field.formfield().to_python(value))


@register.filter()
def field_display(obj, field):
    """
        returns the representation (value or ``get_FIELD_display()``) of  a field

        see `adminactions.utils.get_field_value`_
    """
    return get_field_value(obj, field)


@register.filter
def verbose_name(model_or_queryset, field):
    """
        templatetag wrapper to `adminactions.utils.get_verbose_name`_
    """
    return get_verbose_name(model_or_queryset, field)
