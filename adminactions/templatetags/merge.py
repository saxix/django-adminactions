from django.db import models
from django.db.models import Manager, Model, Field
from django.db.models.query import QuerySet
from django.forms import widgets
from django.forms.util import flatatt
from django.template import Library
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from adminactions.mass_update import OPERATIONS


register = Library()


def get_field_by_path(Model, field_path):
    """
    get a Model and a path to a attribute, return the field


    >>> a = _get_field(Payslip, 'contract.employee.health_ins_type')
    >>> print a
    Health Insurance Type
    """
    parts = field_path.split('.')
    target = parts[0]
    if target in Model._meta.get_all_field_names():
        field_object, model, direct, m2m = Model._meta.get_field_by_name(target)
        if isinstance(field_object, models.fields.related.ForeignKey):
            if parts[1:]:
                return get_field_by_path(field_object.rel.to, '.'.join(parts[1:]))
            else:
                return field_object
        else:
            return field_object
    return None


@register.filter()
def get_field_value(obj, field, usedisplay=True):
    """
        returns a field value or field representation if get_FIELD_display exists
    """
    if isinstance(field, basestring):
        fieldname = field
    elif isinstance(field, models.Field):
        fieldname = field.name

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
