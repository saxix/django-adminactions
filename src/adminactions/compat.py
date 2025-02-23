from __future__ import annotations

from typing import TYPE_CHECKING

import django.db.transaction as t

if TYPE_CHECKING:
    from types import TracebackType


class NoCommit(t.Atomic):
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        super().__exit__(Exception, Exception(), traceback)


def nocommit(using: str | None = None, savepoint: bool = True, durable: bool = False) -> NoCommit:
    return NoCommit(using, savepoint, durable)


try:
    from celery import current_app  # noqa: F401

    celery_present = True
except ImportError:
    celery_present = False
