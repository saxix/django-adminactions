# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.query import QuerySet
from django.template import Library
from adminactions.templatetags.merge import get_field_by_path

register = Library()


@register.filter()
def get_field_value(obj, field, usedisplay=True):
    """
    returns the field value or field representation if get_FIELD_display exists

    :param obj: :class:`django.db.models.Model` instance
    :param field: :class:`django.db.models.Field` instance or ``basestring`` fieldname
    :param usedisplay: boolean if True return the get_FIELD_display() result
    :return: field value

    >>> from django.contrib.auth.models import User, Permission
    >>> p = Permission(name='perm')
    >>> print get_field_value(p, 'name')
    perm

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
def get_verbose_name(model_or_queryset, field):
    """
    return the verbose_name attibute of a field

    typically used in the templates where you can have a dynamic queryset

    :param model_or_queryset:  target object
    :type model_or_queryset: :class:`django.db.models.Model`, :class:`django.db.query.Queryset`

    :param field: field to get the verbose name
    :type field: :class:`django.db.models.Field`, basestring

    :return: translated field verbose name
    :rtype: unicode

    Valid uses:

    >>> from django.contrib.auth.models import User, Permission
    >>> user = User()
    >>> p = Permission()
    >>> print unicode(get_verbose_name(user, 'username'))
    username
    >>> print unicode(get_verbose_name(User, 'username'))
    username
    >>> print unicode(get_verbose_name(User.objects.all(), 'username'))
    username
    >>> print unicode(get_verbose_name(p, 'content_type.model'))
    python model class name
    """

    if isinstance(model_or_queryset, models.Manager):
        model = model_or_queryset.model
    elif isinstance(model_or_queryset, QuerySet):
        model = model_or_queryset.model
    elif isinstance(model_or_queryset, models.Model):
        model = model_or_queryset
    elif type(model_or_queryset) is models.base.ModelBase:
        model = model_or_queryset
    else:
        raise ValueError('`get_verbose_name` expects Manager, Queryset or Model as first parameter (got %s)' % type(model_or_queryset))

    if isinstance(field, basestring):
        field = get_field_by_path(model, field)
    elif isinstance(field, models.Field):
        field = field
    else:
        raise ValueError('`get_verbose_name` field_path muset be string or Field class')

    return field.verbose_name
