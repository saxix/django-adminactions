from django.conf.urls import patterns, url, include, handler500
from django.contrib import admin
import django.contrib.auth.models
from django.contrib.admin import site
import adminactions.actions as actions

if not django.contrib.auth.models.User in site._registry:
    site.register(django.contrib.auth.models.User)

site.add_action(actions.mass_update)
site.add_action(actions.graph_queryset)
site.add_action(actions.export_as_csv)
site.add_action(actions.export_as_fixture)

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)

