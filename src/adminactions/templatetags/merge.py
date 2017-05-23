from __future__ import absolute_import

from django.template import Library

register = Library()


@register.filter(name="widget")
def form_widget(form, fieldname):
    """
    >>> from django.forms import ModelForm, modelform_factory
    >>> from django.contrib.auth.models import User
    >>> f = modelform_factory(User, fields=["username"])
    >>> form_widget(f(instance=User(username="uname")), "username").name
    'username'
    """
    return form[fieldname]


@register.filter(name="errors")
def form_widget_error(form, fieldname):
    """
    >>> from django.forms import ModelForm, modelform_factory
    >>> from django.contrib.auth.models import User
    >>> f = modelform_factory(User, fields=["username"])({}, instance=User())
    >>> form_widget_error(f, "username") == ['This field is required.']
    True
    """
    return form[fieldname].errors


@register.filter(name="value")
def form_widget_value(form, fieldname):
    """
    >>> from django.forms import ModelForm, modelform_factory
    >>> from django.contrib.auth.models import User
    >>> f = modelform_factory(User, fields=["username"])
    >>> form_widget_value(f(instance=User(username="uname")), "username")
    'uname'
    """
    return form[fieldname].value()
