from django.urls import path

from .views import format_date

urlpatterns = (
    path('s/format/date/', format_date, name='adminactions.format_date'),
)
