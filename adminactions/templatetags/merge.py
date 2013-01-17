from django.db import models
from django.db.models import Manager, Model
from django.db.models.query import QuerySet
from django.template import Library
from adminactions.utils import get_field_by_path


register = Library()


@register.filter(name="widget")
def form_widget(form, fieldname):
    return form[fieldname]


@register.filter(name="errors")
def form_widget_error(form, fieldname):
    return form[fieldname].errors


@register.filter(name="value")
def form_widget_value(form, fieldname):
    return form[fieldname].value()
