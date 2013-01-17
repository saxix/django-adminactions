# -*- coding: utf-8 -*-
import datetime
from django import forms
from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet
from django.template import Library
from django.utils.formats import get_format
from adminactions.templatetags.merge import get_field_by_path
from adminactions.utils import get_field_value


register = Library()

@register.filter()
def raw_value(obj, field):
    value = get_field_value(obj, field, False)
#    return value
    return str(field.formfield().to_python(value))
#    if settings.USE_L10N:
#        if isinstance(value, datetime.datetime):
#            fmt = get_format('DATETIME_INPUT_FORMATS')[0]
#            return value.strftime(fmt)
#        elif isinstance(value, datetime.date):
#            fmt = get_format('DATE_INPUT_FORMATS')[0]
#            return value.strftime(fmt)
#    return value
#    return str(get_field_value(obj, field, False))

#@register.filter()
#def raw_value(obj, field):
#    return field.formfield(form_class=forms.CharField).widget.render("", get_field_value(obj, field, False))
#    .render("", get_field_value(obj, field, False))



@register.filter()
def field_display(obj, field):
    return get_field_value(obj, field)


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
