from django.db import models

def clone_model(model):
    new_kwargs = dict([(fld.name, getattr(model, fld.name)) for fld in model._meta.fields])
    return model.__class__(**new_kwargs)


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

def get_field_by_path(model, field_path):
    """
    get a Model class or instance and a path to a attribute, returns the field object

    :param model: :class:`django.db.models.Model`
    :param field_path: string path to the field
    :return: :class:`django.db.models.Field`


    >>> from django.contrib.auth.models import User, Permission

    >>> p = Permission(name='perm')
    >>> f = get_field_by_path(Permission, 'content_type')
    >>> print f
    <django.db.models.fields.related.ForeignKey: content_type>

    >>> p = Permission(name='perm')
    >>> f = get_field_by_path(p, 'content_type.app_label')
    >>> print f
    <django.db.models.fields.CharField: app_label>

    """
    parts = field_path.split('.')
    target = parts[0]
    if target in model._meta.get_all_field_names():
        field_object, model, direct, m2m = model._meta.get_field_by_name(target)
        if isinstance(field_object, models.fields.related.ForeignKey):
            if parts[1:]:
                return get_field_by_path(field_object.rel.to, '.'.join(parts[1:]))
            else:
                return field_object
        else:
            return field_object
    return None


def flatten(iterable):
    """
    flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    :param sequence: any object that implements iterable protocol (see: :ref:`typeiter`)
    :return: list

    Examples:

    >>> from adminactions.utils import flatten
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]

    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, (8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]"""

    result = list()
    for el in iterable:
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return list(result)
