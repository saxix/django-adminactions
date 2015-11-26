from __future__ import absolute_import
from django.contrib import admin
from django.conf.urls import include, url
from adminactions import actions
import adminactions.urls

admin.autodiscover()
actions.add_to_site(admin.site)

urlpatterns = (
    url(r'admin/', include(admin.site.urls)),
    url(r'as/', include(adminactions.urls)),
    url(r'', include(admin.site.urls)),
)
