import logging

from celery import shared_task  # noqa
from django.apps import apps

logger = logging.getLogger(__name__)


@shared_task()
def mass_update_task(model, ids, rules, validate, clean, user_pk):
    from adminactions.mass_update import mass_update_execute

    try:
        model = apps.get_model(*model.split("."))
        queryset = model.objects.filter(id__in=ids)
        mass_update_execute(queryset, rules, validate, clean, user_pk=user_pk)
    except Exception as e:
        logger.exception(e)
        raise
