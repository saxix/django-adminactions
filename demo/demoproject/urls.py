import adminactions.urls
import django.contrib.admin
import django.contrib.admin.sites
from django.contrib.auth.models import User
from django.conf.urls import patterns, include
from adminactions import actions
from .demoapp.admin import DemoModelAdmin
from .demoapp.models import DemoModel


class PublicAdminSite(django.contrib.admin.sites.AdminSite):
    def has_permission(self, request):
        request.user = User.objects.get_or_create(username='sax')[0]
        return True


public_site = PublicAdminSite()
django.contrib.admin.autodiscover()
public_site.register(DemoModel, DemoModelAdmin)
public_site.register(User)

actions.add_to_site(public_site)

urlpatterns = patterns('',
                       (r'^adm/', include(include(adminactions.urls))),
                       (r'', include(include(public_site.urls))),
                       (r'^admin/', include(include(public_site.urls))))
