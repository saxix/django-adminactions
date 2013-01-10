from django.forms import widgets
from django.forms.util import flatatt
from django.template import Library
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from adminactions.mass_update import OPERATIONS


register = Library()


@register.simple_tag
def fields_values(d, k):
    """
    >>> data = {'name1': ['value1.1', 'value1.2'], 'name2': ['value2.1', 'value2.2'], }
    >>> field_values(data, 'name1')
    value1.1, value1.2
    """
    values = d.get(k, [])
    return ",".join(map(str, values))


@register.simple_tag
def link_fields_values(d, k):
    """
    >>> data = {'name1': ['value1.1', 'value1.2'], 'name2': ['value2.1', 'value2.2'], }
    >>> link_fields_values(data, 'name1')
    u'<a href="#" class="fastfieldvalue name1">value1.1</a>, <a href="#" class="fastfieldvalue name1">value1.2</a>'
    """
    ret = []
    for v in d.get(k, []):
        if v == '': # ignore empty
            continue
        ret.append('<a href="#" class="fastfieldvalue %s value">%s</a>' % (k, force_unicode(v)))

    return mark_safe(", ".join(ret))


@register.simple_tag(takes_context=True)
def checkbox_enabler(context, field):
    selected = context['selected_fields']
    name = "chk_id_%s" % field.name
    checked = {True: 'checked="checked"', False: ''}[name in selected]
    return mark_safe('<input type="checkbox" name="%s" %s class="enabler">' % (name, checked))


class SelectOptionsAttribute(widgets.Select):
    """
        Select widget with the capability to render option's attributes
    """
    def __init__(self, attrs=None, choices=(), options_attributes=None):
        self.options_attributes = options_attributes or {}
        super(SelectOptionsAttribute, self).__init__(attrs, choices)

    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_unicode(option_value)
        attrs = flatatt(self.options_attributes.get(option_value, {}))
        if option_value in selected_choices:
            selected_html = u' selected="selected"'
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        return u'<option%s value="%s"%s>%s</option>' % (
            attrs,
            escape(option_value), selected_html,
            conditional_escape(force_unicode(option_label)))


@register.simple_tag
def field_function(model, form_field):
    model_object, model, direct, m2m = model._meta.get_field_by_name(form_field.name)
    attrs = {'class': 'func_select'}
    options_attrs = {}
    choices = []
    classes = {True: 'param', False: 'noparam'}
    for label, (__, param, enabler, __) in OPERATIONS.get_for_field(model_object).items():
        options_attrs[label] = {'class': classes[param], 'label': label}
        choices.append((label, label))
    return SelectOptionsAttribute(attrs, choices, options_attrs).render("func_id_%s" % form_field.name, "")
