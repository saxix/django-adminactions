import django.db.transaction as t


class NoCommit(t.Atomic):
    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(Exception, Exception(), None)


def nocommit(using=None, savepoint=True, durable=False):
    return NoCommit(using, savepoint, durable)


try:
    from celery import current_app  # noqa

    celery_present = True
except ImportError:
    celery_present = False
