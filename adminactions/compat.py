from contextlib import contextmanager
import django.db.transaction as t

try:  # django >= 1.6
    from django.db.transaction import atomic  # noqa

    @contextmanager
    def nocommit(using=None):
        backup = t.get_autocommit(using)
        t.set_autocommit(False, using)
        t.enter_transaction_management(managed=True, using=using)
        yield
        t.rollback(using)
        t.leave_transaction_management(using)
        t.set_autocommit(backup, using)

except ImportError:  # django <=1.5

    @contextmanager
    def nocommit(using=None):
        t.enter_transaction_management(using=using)
        t.managed(True, using=using)
        yield
        t.rollback()
        t.leave_transaction_management(using=using)
