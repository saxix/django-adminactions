import logging

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from utils import user_grant_permission

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("action", ['export_as_csv', 'export_as_xls', 'merge',
                                    'export_as_fixture', 'export_delete_tree',
                                    'graph_queryset', 'mass_update'])
@pytest.mark.django_db()
def test_permission_needed(app, admin, demomodels, action):
    permission_mapping = {'export_as_csv': 'adminactions_export',
                          'export_as_fixture': 'adminactions_export',
                          'export_as_xls': 'adminactions_export',
                          'export_delete_tree': 'adminactions_export',
                          'mass_update': 'adminactions_massupdate',
                          'merge': 'adminactions_merge',
                          'graph_queryset': 'adminactions_chart',
                          }
    perm = "demo.{}_demomodel".format(permission_mapping[action])
    url = reverse('admin:demo_demomodel_changelist')
    pks = [demomodels[0].pk, demomodels[1].pk]
    with user_grant_permission(admin, ['demo.change_demomodel']):
        res = app.post(url, params=[('action', action),
                             ('_selected_action', pks)],
                       extra_environ={'wsgi.url_scheme': 'https'},
                       user=admin.username,
                       expect_errors=True)
        assert res.status_code == 302
        res = res.follow()
        assert 'Sorry you do not have rights to execute this action' in [str(m) for m in res.context['messages']]

        with user_grant_permission(admin, [perm]):
            res = app.post(url, params=[('action', action),
                                 ('_selected_action', pks)],
                           extra_environ={'wsgi.url_scheme': 'https'},
                           user=admin.username,
                           expect_errors=True)
            assert res.status_code == 200


@pytest.mark.django_db()
def test_permissions(admin):
    assert Permission.objects.filter(codename__startswith='adminactions').count() == 45

    with user_grant_permission(admin, ['demo.adminactions_export_demomodel']):
        assert admin.get_all_permissions() == set([u'demo.adminactions_export_demomodel'])
