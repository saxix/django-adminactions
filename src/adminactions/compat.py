from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager

import django
import django.db.transaction as t

version = django.VERSION[:2]

if version <= (1, 5):  # noqa

    @contextmanager
    def nocommit(using=None):
        t.enter_transaction_management(using=using)
        t.managed(True, using=using)
        yield
        t.rollback()
        t.leave_transaction_management(using=using)

    class atomic(object):
        def __init__(self, using=None):
            self.using = using

        def __enter__(self):
            t.enter_transaction_management(using=self.using)
            t.managed(True, using=self.using)

        def __exit__(self, exc_type, exc_value, traceback):
            try:
                if exc_type is not None:
                    if t.is_dirty(using=self.using):
                        t.rollback(using=self.using)
                else:
                    if t.is_dirty(using=self.using):
                        try:
                            t.commit(using=self.using)
                        except:
                            t.rollback(using=self.using)
                            raise
            finally:
                t.leave_transaction_management(using=self.using)


else:
    from django.db.transaction import atomic  # noqa

    class NoCommit(t.Atomic):
        def __exit__(self, exc_type, exc_value, traceback):
            super(NoCommit, self).__exit__(Exception, Exception(), None)

    def nocommit(using=None, savepoint=True):
        return NoCommit(using, savepoint)


# Model._meta compatibility
if version >= (1, 10):  # noqa
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
                    # For complete backwards compatibility, you may want to exclude
                    # GenericForeignKey from the results.
                    if not (field.many_to_one and field.related_model is None))))
# elif version >= (1, 9):  # noqa
    # pass
# elif version >= (1, 8):  # noqa
    # pass
# elif version >= (1, 7):  # noqa
    # pass
# elif version >= (1, 6):  # noqa
    # pass
# elif version >= (1, 5):  # noqa
    # pass
elif version >= (1, 4):  # noqa
    def get_all_related_objects(model):
        return model._meta.get_all_related_objects()

    def get_all_field_names(model):
        return model._meta.get_all_field_names()

    def get_field_by_name(model, name):
        return model._meta.get_field_by_name(name)

    def model_has_field(model, field_name):
        return field_name in model._meta.get_all_field_names()
