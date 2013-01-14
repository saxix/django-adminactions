from django.db import models


def get_field_from_path(Model, field_path):
    """
    get a Model and a path to a attribute, return the field


    >>> a = get_field_from_path(Payslip, 'contract.employee.health_ins_type')
    >>> print a
    Health Insurance Type
    """
    parts = field_path.split('.')
    target = parts[0]
    if target in Model._meta.get_all_field_names():
        field_object, model, direct, m2m = Model._meta.get_field_by_name(target)
        if isinstance(field_object, models.fields.related.ForeignKey):
            if parts[1:]:
                return get_field_from_path(field_object.rel.to, '.'.join(parts[1:]))
            else:
                return field_object
        else:
            return field_object
    return None



def flatten(x):
    """flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples:

    >>> from adminactions.utils import flatten
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]

    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, (8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]"""

    result = []
    for el in x:
        #if isinstance(el, (list, tuple)):
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return list(result)
