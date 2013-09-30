from django.contrib import admin
from django.conf.urls import patterns, include
from django.contrib.auth.models import Permission
from adminactions import actions
import adminactions.urls
from demoproject.demoapp.admin import DemoModelAdmin
from demoproject.demoapp.models import DemoModel


admin.autodiscover()
actions.add_to_site(admin.site)

urlpatterns = patterns('',
                       (r'', include(admin.site.urls)),
                       (r'as/', include(adminactions.urls)),
                       )
