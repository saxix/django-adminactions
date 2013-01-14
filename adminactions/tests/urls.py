import django.contrib.auth.models
from django.conf.urls import patterns, url, include, handler500
from django.contrib import admin
import adminactions.actions as actions

if not django.contrib.auth.models.User in admin.site._registry:
    admin.site.register(django.contrib.auth.models.User)

if not django.contrib.auth.models.Permission in admin.site._registry:
    admin.site.register(django.contrib.auth.models.Permission)

actions.add_to_site(admin.site)

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
)

