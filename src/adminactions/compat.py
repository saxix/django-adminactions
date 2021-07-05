import django
import django.db.transaction as t
from functools import partial


class NoCommit(t.Atomic):
    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(Exception, Exception(), None)


if django.VERSION >= (3, 2):
    def nocommit(using=None, savepoint=True, durable=False):
        return NoCommit(using, savepoint, durable)
else:
    def nocommit(using=None, savepoint=True):
        return NoCommit(using, savepoint)


def get_field_by_name(model, name):
    field = model._meta.get_field(name)
    direct = not field.auto_created or field.concrete
    return field, field.model, direct, field.many_to_many


def model_has_field(model, field_name):
    return field_name in [f.name for f in model._meta.get_fields()]


def get_all_related_objects(model):
    return [f for f in model._meta.get_fields()
            if (f.one_to_many or f.one_to_one) and f.auto_created]


def get_all_field_names(model):
    from itertools import chain
    return list(set(chain.from_iterable((field.name, field.attname)
                                        if hasattr(field, 'attname') else (field.name,)
                                        for field in model._meta.get_fields()
                                        if not (field.many_to_one and field.related_model is None))))


def curry(func, *a, **kw):
    return partial(func, *a, **kw)
