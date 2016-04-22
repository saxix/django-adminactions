from __future__ import absolute_import

from django.conf.urls import include, url
from django.contrib import admin

import adminactions.urls
from adminactions import actions

admin.autodiscover()
actions.add_to_site(admin.site)

urlpatterns = (
    url(r'admin/', include(admin.site.urls)),
    url(r'as/', include(adminactions.urls)),
    url(r'', include(admin.site.urls)),
)
