from django.db import models
from django.db.models import Manager, Model
from django.db.models.query import QuerySet
from django.template import Library
from adminactions.utils import get_field_by_path


register = Library()


@register.filter()
def get_field_value(obj, field, usedisplay=True):
    """
        returns a field value or field representation if get_FIELD_display exists
    """
    if isinstance(field, basestring):
        fieldname = field
    elif isinstance(field, models.Field):
        fieldname = field.name
    else:
        raise ValueError('Invalid value for parameter `field`: Should be a field name or a Field instance ')

    if hasattr(obj, 'get_%s_display' % fieldname) and usedisplay:
        value = getattr(obj, 'get_%s_display' % fieldname)()
    else:
        value = getattr(obj, fieldname)

    return value


@register.filter(name="verbose_name")
def get_verbose_name(model_or_queryset, field_path):
    if isinstance(model_or_queryset, Manager):
        model = model_or_queryset.model
    elif isinstance(model_or_queryset, QuerySet):
        model = model_or_queryset.model
    elif isinstance(model_or_queryset, Model):
        model = model_or_queryset
    else:
        raise AttributeError('`get_verbose_name` expects Manager, Queryset or Model as first parameter')

    if isinstance(field_path, basestring):
        field = get_field_by_path(model, field_path)
    elif isinstance(field_path, models.Field):
        field = field_path

    return field.verbose_name
