# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.conf.urls import include, url
from django.contrib import admin

from adminactions import actions

admin.autodiscover()
actions.add_to_site(admin.site)

urlpatterns = (
    url(r'admin/', admin.site.urls),
    url(r'as/', include('adminactions.urls')),
    url(r'', admin.site.urls),
)
