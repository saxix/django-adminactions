from django.forms import widgets
from django.forms.utils import flatatt
from django.template import Library
from django.utils.encoding import smart_str
from django.utils.html import conditional_escape, escape
from django.utils.safestring import mark_safe

from adminactions.utils import get_field_by_name

register = Library()


@register.simple_tag
def fields_values(d, k):
    """
    >>> data = {'name1': ['value1.1', 'value1.2'], 'name2': ['value2.1', 'value2.2'], }
    >>> print(fields_values(data, 'name1'))
    value1.1,value1.2
    """
    values = d.get(k, [])
    return ",".join(map(str, values))


@register.simple_tag
def link_fields_values(d, field_name):
    """
    >>> data = {'name1': [(1, 'value1.1'), (11, 'value1.2')],
    ...         'name2': [(2, 'value2.1'), (22, 'value2.2')], }
    >>> print(link_fields_values(data, 'name1'))
    <a name="name1_fastfieldvalue"><a href="#name1_fastfieldvalue" \
data-value="1" class="fastfieldvalue name1 value">value1.1</a>, \
<a name="name1_fastfieldvalue">\
<a href="#name1_fastfieldvalue" data-value="11" class="fastfieldvalue name1 value">value1.2</a>
    """
    ret = []
    name = "{0}_fastfieldvalue".format(field_name)

    for el in d.get(field_name, []):
        try:
            value, label = el
        except (TypeError, ValueError):
            value, label = el, el

        if label == '':  # ignore empty
            continue
        ret.append('<a name="{name}"><a href="#{name}" '
                   'data-value="{value}" '
                   'class="fastfieldvalue {field} '
                   'value">{label}</a>'.format(name=name,
                                               value=value,
                                               field=field_name,
                                               label=str(label)))

    return mark_safe(", ".join(ret))


@register.simple_tag(takes_context=True)
def checkbox_enabler(context, field):
    form = context['adminform'].form
    name = "chk_id_%s" % field.name
    checked = ""
    if form.is_bound:
        chk = form.cleaned_data.get(name, False)
        checked = {True: 'checked="checked"', False: ''}[chk]
    return mark_safe('<input type="checkbox" name="%s" %s class="enabler">' % (name, checked))


class SelectOptionsAttribute(widgets.Select):
    """
        Select widget with the capability to render option's attributes

    >>> opt = SelectOptionsAttribute()
    >>> opt.render_option(["1"], 1, "a") == '<option value="1" selected="selected">a</option>'
    True
    >>> opt.render_option([], 1, "a") == '<option value="1">a</option>'
    True
    """

    def __init__(self, attrs=None, choices=(), options_attributes=None):
        # self.options_attributes = options_attributes or {}
        super().__init__(attrs, choices)

    # def render_option(self, selected_choices, option_value, option_label):
    #     # FIXME: remove me (print)
    #     print(111, "massupdate.py:85 (render_option)", 11111)
    #     print(111, "massupdate.py:85 (render_option)", 11111)
    #     print(111, "massupdate.py:85 (render_option)", 11111)
    #     print(111, "massupdate.py:85 (render_option)", 11111)
    #     print(111, "massupdate.py:85 (render_option)", selected_choices)
    #     option_value = smart_str(option_value)
    #     attrs = flatatt(self.options_attributes.get(option_value, {}))
    #     if option_value in selected_choices:
    #         selected_html = u' selected="selected"'
    #         if not self.allow_multiple_selected:
    #             # Only allow for a single selection.
    #             selected_choices.remove(option_value)
    #     else:
    #         selected_html = ''
    #     return u'<option%s value="%s"%s>1111111 %s</option>' % (
    #         attrs,
    #         escape(option_value), selected_html,
    #         conditional_escape(smart_str(option_label)))


@register.simple_tag(takes_context=True)
def field_function(context, model, form_field):
    from adminactions.mass_update import OPERATIONS
    model_field, model, direct, m2m = get_field_by_name(model, form_field.name)
    attrs = {'class': 'func_select'}
    options_attrs = {}
    choices = []
    classes = {True: 'param', False: 'noparam'}
    form = context['adminform'].form
    value = ""
    if form.is_bound:
        value = form.cleaned_data.get("func_id_%s" % form_field.name, "")

    for label, (__, param, enabler, __) in list(OPERATIONS.get_for_field(model_field).items()):
        options_attrs[label] = {'class': classes[param], 'label': label}
        choices.append((label, label))
    return widgets.Select(attrs, choices).render("func_id_%s" % form_field.name,
                                                                        value)
