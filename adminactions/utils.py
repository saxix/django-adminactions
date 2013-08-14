from django.db import models
from django.db.models.query import QuerySet


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


def get_copy_of_instance(instance):
    return instance.__class__.objects.get(pk=instance.pk)


def get_field_value(obj, field, usedisplay=True):
    """
    returns the field value or field representation if get_FIELD_display exists

    :param obj: :class:`django.db.models.Model` instance
    :param field: :class:`django.db.models.Field` instance or ``basestring`` fieldname
    :param usedisplay: boolean if True return the get_FIELD_display() result
    :return: field value

    >>> from django.contrib.auth.models import Permission
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


    >>> from django.contrib.auth.models import Permission

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
    >>> print unicode(get_verbose_name(user, 'username'))
    username
    >>> print unicode(get_verbose_name(User, 'username'))
    username
    >>> print unicode(get_verbose_name(User.objects.all(), 'username'))
    username
    >>> print unicode(get_verbose_name(User.objects, 'username'))
    username
    >>> print unicode(get_verbose_name(User.objects, user._meta.get_field_by_name('username')[0]))
    username
    >>> print unicode(get_verbose_name(p, 'content_type.model'))
    python model class name
    >>> get_verbose_name(object, 'aaa')
    Traceback (most recent call last):
    ...
    ValueError: `get_verbose_name` expects Manager, Queryset or Model as first parameter (got <type 'type'>)
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

    if isinstance(field, basestring):
        field = get_field_by_path(model, field)
    elif isinstance(field, models.Field):
        field = field
    else:
        raise ValueError('`get_verbose_name` field_path muset be string or Field class')

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
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return list(result)
