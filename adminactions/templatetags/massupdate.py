from django.template import Library
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

register = Library()

def fields_values(d, k):
    """
    Returns the string contained in the setting ADMIN_MEDIA_PREFIX.
    """
    values = d.get(k,[])
    return ",".join(map(str,values))

fields_values = register.simple_tag(fields_values)


def link_fields_values(d, k):
    """
    >>> data = {'name1': ['value1.1', 'value1.2'], 'name2': ['value2.1', 'value2.2'], }
    >>> link_fields_values(data, 'name1')
    u'<a href="#" class="fastfieldvalue name1">value1.1</a>, <a href="#" class="fastfieldvalue name1">value1.2</a>'
    """
    ret = []
    for v in d.get(k,[]):
        if v == '': # ignore empty
            continue
        ret.append('<a href="#" class="fastfieldvalue %s value">%s</a>' % (k, force_unicode(v)))
        
    return mark_safe(", ".join(ret))

link_fields_values = register.simple_tag(link_fields_values)
