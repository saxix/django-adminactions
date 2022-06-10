import logging
from celery.app import default_app
from django.apps import apps

logger = logging.getLogger(__name__)


@default_app.task()
def mass_update_task(model, ids, rules, validate, clean):
    from adminactions.mass_update import mass_update_execute
    try:
        model = apps.get_model(*model.split("."))
        queryset = model.objects.filter(id__in=ids)
        mass_update_execute(queryset, rules, validate, clean)
    except Exception as e:
        logger.exception(e)
        raise
