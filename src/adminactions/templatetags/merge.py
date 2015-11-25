from __future__ import absolute_import

from django.template import Library

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
