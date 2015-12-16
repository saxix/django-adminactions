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
