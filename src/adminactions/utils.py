from django.db import models
from django.db.models.query import QuerySet
from django.utils.encoding import smart_text

from adminactions.compat import get_all_field_names, get_field_by_name


def clone_instance(instance, fieldnames=None):
    """
        returns a copy of the passed instance.

        .. warning: All fields are copied, even primary key

    :param instance: :py:class:`django.db.models.Model` instance
    :return: :py:class:`django.db.models.Model` instance
    """

    if fieldnames is None:
        fieldnames = [fld.name for fld in instance._meta.fields]

    new_kwargs = dict([(name, getattr(instance, name)) for name in fieldnames])
    return instance.__class__(**new_kwargs)


# def get_copy_of_instance(instance):
# return instance.__class__.objects.get(pk=instance.pk)


def get_attr(obj, attr, default=None):
    """Recursive get object's attribute. May use dot notation.

    >>> class C(object): pass
    >>> a = C()
    >>> a.b = C()
    >>> a.b.c = 4
    >>> get_attr(a, 'b.c')
    4

    >>> get_attr(a, 'b.c.y', None)

    >>> get_attr(a, 'b.c.y', 1)
    1
    """
    if '.' not in attr:
        ret = getattr(obj, attr, default)
    else:
        L = attr.split('.')
        ret = get_attr(getattr(obj, L[0], default), '.'.join(L[1:]), default)

    if isinstance(ret, BaseException):
        raise ret
    return ret


def getattr_or_item(obj, name):
    """
    works indifferently on dict or objects, retrieving the
    'name' attribute or item

    :param obj:  dict or object
    :param name: attribute or item name
    :return:
    >>> from django.contrib.auth.models import Permission
    >>> p = Permission(name='perm')
    >>> d ={'one': 1, 'two': 2}
    >>> getattr_or_item(d, 'one')
    1
    >>> print(getattr_or_item(p, 'name'))
    perm
    >>> getattr_or_item(dict, "!!!")
    Traceback (most recent call last):
        ...
    AttributeError: type object has no attribute/item '!!!'
    """
    try:
        ret = get_attr(obj, name, AttributeError())
    except AttributeError:
        try:
            ret = obj[name]
        except (KeyError, TypeError):
            raise AttributeError("%s object has no attribute/item '%s'" % (obj.__class__.__name__, name))
    return ret


def get_field_value(obj, field, usedisplay=True, raw_callable=False):
    """
    returns the field value or field representation if get_FIELD_display exists

    :param obj: :class:`django.db.models.Model` instance
    :param field: :class:`django.db.models.Field` instance or ``basestring`` fieldname
    :param usedisplay: boolean if True return the get_FIELD_display() result
    :return: field value

    >>> from django.contrib.auth.models import Permission
    >>> p = Permission(name='perm')
    >>> get_field_value(p, 'name') == 'perm'
    True
    >>> get_field_value(p, None)
    Traceback (most recent call last):
        ...
    ValueError: Invalid value for parameter `field`: Should be a field name or a Field instance
    """
    if isinstance(field, str):
        fieldname = field
    elif isinstance(field, models.Field):
        fieldname = field.name
    else:
        raise ValueError('Invalid value for parameter `field`: Should be a field name or a Field instance')

    if usedisplay and hasattr(obj, 'get_%s_display' % fieldname):
        value = getattr(obj, 'get_%s_display' % fieldname)()
    else:
        value = getattr_or_item(obj, fieldname)

    if hasattr(value, 'all'):
        value = ';'.join(smart_text(obj) for obj in value.all())
    if not raw_callable and callable(value):
        value = value()

    if isinstance(value, models.Model):
        return smart_text(value)

    # if isinstance(obj, Model):
    #     field = get_field_by_path(obj, fieldname)
    #     if isinstance(field, ForeignKey):
    #         return unicode(value)
    if isinstance(value, str):
        value = smart_text(value)

    return value


def get_field_by_path(model, field_path):
    """
    get a Model class or instance and a path to a attribute, returns the field object

    :param model: :class:`django.db.models.Model`
    :param field_path: string path to the field
    :return: :class:`django.db.models.Field`


    >>> from django.contrib.auth.models import Permission

    >>> p = Permission(name='perm')
    >>> get_field_by_path(Permission, 'content_type').name
    'content_type'
    >>> p = Permission(name='perm')
    >>> get_field_by_path(p, 'content_type.app_label').name
    'app_label'
    """
    parts = field_path.split('.')
    target = parts[0]
    if target in get_all_field_names(model):
        field_object, model, direct, m2m = get_field_by_name(model, target)
        if isinstance(field_object, models.fields.related.ForeignKey):
            if parts[1:]:
                return get_field_by_path(field_object.related_model, '.'.join(parts[1:]))
            else:
                return field_object
        else:
            return field_object
    return None


def get_verbose_name(model_or_queryset, field):
    """
    returns the value of the ``verbose_name`` of a field

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
    >>> get_verbose_name(user, 'username') == 'username'
    True
    >>> get_verbose_name(User, 'username') == 'username'
    True
    >>> get_verbose_name(User.objects.all(), 'username') == 'username'
    True
    >>> get_verbose_name(User.objects, 'username') == 'username'
    True
    >>> get_verbose_name(User.objects, user._meta.fields[0]) == 'ID'
    True
    >>> get_verbose_name(p, 'content_type.model') == 'python model class name'
    True
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
        raise ValueError('`get_verbose_name` expects Manager, Queryset or Model as first parameter (got %s)' % type(
            model_or_queryset))

    if isinstance(field, str):
        field = get_field_by_path(model, field)
    elif isinstance(field, models.Field):
        field = field
    else:
        raise ValueError('`get_verbose_name` field_path must be string or Field class')

    return field.verbose_name


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
        if hasattr(el, "__iter__") and not isinstance(el, str):
            result.extend(flatten(el))
        else:
            result.append(el)
    return list(result)
