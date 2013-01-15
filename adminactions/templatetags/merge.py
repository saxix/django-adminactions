from django.db import models
from django.db.models import Manager, Model
from django.db.models.query import QuerySet
from django.template import Library
from adminactions.utils import get_field_by_path


register = Library()
