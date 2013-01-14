# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.query import QuerySet
from django.template import Library
from adminactions.templatetags.merge import get_field_by_path
from django.utils.translation import ugettext_lazy as _


register = Library()

#
#def get_field_by_path(model, field_path):
#    """
#    get a Model and a path to a attribute, return the django.dm.models.Field
#
#    :param Model django.db.models.Model
#    :param fieldpath  django.db.models.Model
#
#    :return
#
#    >>> a = get_field_by_path(User, 'contract.employee.health_ins_type')
#    >>> print a
#    Health Insurance Type
#    """
#    parts = field_path.split('.')
#    target = parts[0]
#    if target in model._meta.get_all_field_names():
#        field_object, model, direct, m2m = model._meta.get_field_by_name(target)
#        if isinstance(field_object, models.fields.related.ForeignKey):
#            if parts[1:]:
#                return get_field_by_path(field_object.rel.to, '.'.join(parts[1:]))
#            else:
#                return field_object
#        else:
#            return field_object
#    return None


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
    if isinstance(model_or_queryset, models.Manager):
        model = model_or_queryset.model
    elif isinstance(model_or_queryset, QuerySet):
        model = model_or_queryset.model
    elif isinstance(model_or_queryset, models.Model):
        model = model_or_queryset
    else:
        raise ValueError('`get_verbose_name` expects Manager, Queryset or Model as first parameter')

    if isinstance(field_path, basestring):
        field = get_field_by_path(model, field_path)
    elif isinstance(field_path, models.Field):
        field = field_path
    else:
        raise ValueError('`get_verbose_name` field_path muset be string or Field class')

    return field.verbose_name
