from django.contrib import admin
from django.conf.urls import patterns, include
from adminactions import actions
import adminactions.urls

try:
    from django.apps import AppConfig
    import django

    django.setup()
except ImportError:
    pass

admin.autodiscover()
actions.add_to_site(admin.site)

urlpatterns = patterns('',
                       (r'', include(admin.site.urls)),
                       (r'admin/', include(admin.site.urls)),
                       (r'as/', include(adminactions.urls)),
                       )
