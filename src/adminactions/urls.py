from django.urls import re_path

from .views import format_date

urlpatterns = (
    re_path(r'^s/format/date/$', format_date, name='adminactions.format_date'),
)
