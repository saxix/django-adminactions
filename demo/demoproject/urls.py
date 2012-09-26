import django.contrib.admin
import django.contrib.admin.sites
from django.contrib.auth.models import User
from django.conf.urls import patterns, include, url
from adminactions import actions


class PublicAdminSite(django.contrib.admin.sites.AdminSite):
    def has_permission(self, request):
        request.user = User.objects.get_or_create(username='sax')[0]
        return True

site = PublicAdminSite()
django.contrib.admin.site = django.contrib.admin.sites.site = site
django.contrib.admin.autodiscover()

site.add_action(actions.mass_update)
site.add_action(actions.graph_queryset)
site.add_action(actions.export_as_csv)
site.add_action(actions.export_as_fixture)

urlpatterns = patterns('',
    (r'', include(include(site.urls))),
#    (r'', include(demoapp.urls)),
    url(r'^admin/', include(site.urls)),
)
