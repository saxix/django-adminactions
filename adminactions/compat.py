
from contextlib import contextmanager

try:
    from django.db.transaction import atomic
    import django.db.transaction as t

    @contextmanager
    def commit_manually():
        t.set_autocommit(False)
        yield
        t.set_autocommit(True)

    @contextmanager
    def nocommit():
        t.set_autocommit(False)
        yield
        rollback()
        t.set_autocommit(True)

except:
    from django.db.transaction import commit_on_success as atomic, rollback, commit_manually
    import django.db.transaction as t

    @contextmanager
    def nocommit(using=None):
        t.enter_transaction_management(using=using)
        yield
        rollback()
        t.leave_transaction_management(using=using)
