from django.contrib import admin
from django.conf.urls import patterns, include
from adminactions import actions
import adminactions.urls


admin.autodiscover()
actions.add_to_site(admin.site)

urlpatterns = patterns('',
                       (r'admin/', include(admin.site.urls)),
                       (r'as/', include(adminactions.urls)),
                       (r'', include(admin.site.urls)),
                       )

