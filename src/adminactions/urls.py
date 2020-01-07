# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import format_date

urlpatterns = (
    url(r'^s/format/date/$', format_date, name='adminactions.format_date'),
)
