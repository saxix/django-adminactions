
from contextlib import contextmanager

try:
    from django.db.transaction import atomic, rollback
    import django.db.transaction as t

    @contextmanager
    def commit_manually():
        t.set_autocommit(False)
        yield
        t.set_autocommit(True)

except:
    from django.db.transaction import commit_manually, rollback
