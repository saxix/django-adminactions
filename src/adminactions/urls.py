from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from adminactions.views import format_date

urlpatterns = (url(r'^s/format/date/$', format_date, name='adminactions.format_date'),)
