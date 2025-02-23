import logging
from typing import Any

from celery import shared_task
from django.apps import apps
from django.db.models.base import Model

logger = logging.getLogger(__name__)


@shared_task()
def mass_update_task(
    model: Model,
    ids: list[Any],
    rules: dict[str, tuple[callable, Any]],
    validate: bool,
    clean: bool,
    user_pk: Any,
) -> None:
    from adminactions.mass_update import mass_update_execute  # noqa: PLC0415

    try:
        model = apps.get_model(*model.split("."))
        queryset = model.objects.filter(id__in=ids)
        mass_update_execute(queryset, rules, validate, clean, user_pk=user_pk)
    except Exception as e:
        logger.exception(e)
        raise
