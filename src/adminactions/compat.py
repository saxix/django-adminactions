import django
import django.db.transaction as t


class NoCommit(t.Atomic):
    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(Exception, Exception(), None)


if django.VERSION >= (3, 2):
    def nocommit(using=None, savepoint=True, durable=False):
        return NoCommit(using, savepoint, durable)
else:
    def nocommit(using=None, savepoint=True):
        return NoCommit(using, savepoint)

