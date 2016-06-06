from __future__ import absolute_import

from six.moves import range

import django
import pytest
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G
from django_webtest import WebTest
from utils import CheckSignalsMixin, SelectRowsMixin, user_grant_permission


@pytest.mark.skipif(django.VERSION[:2] > (1, 9), reason="skip if django > 1.9")
class TestGraph(SelectRowsMixin, CheckSignalsMixin, WebTest):
    fixtures = ['adminactions', 'demoproject']
    urls = 'demo.urls'
    sender_model = User
    action_name = 'graph_queryset'
    _selected_rows = [0, 1]

    def setUp(self):
        super(TestGraph, self).setUp()
        self.user = G(User, username='user', is_staff=True, is_active=True)

    def _run_action(self, steps=2):
        # with user_grant_permission(self.user, ['demo.change_demomodel', 'demo.adminactions_massupdate_demomodel']):

        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_chart_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            if steps >= 1:
                form = res.forms['changelist-form']
                form['action'] = 'graph_queryset'
                self._select_rows(form)
                # form.set('_selected_action', True, 0)
                # form.set('_selected_action', True, 1)
                res = form.submit()
            if steps >= 2:
                res.form['axes_x'] = 'username'
                res = res.form.submit('apply')

            return res

    def test_graph_apply(self):
        url = reverse('admin:auth_user_changelist')
        res = self.app.get(url, user='sax')
        form = res.forms['changelist-form']
        form['action'] = 'graph_queryset'
        for i in range(0, 11):
            form.set('_selected_action', True, i)
        res = form.submit()
        res.form['graph_type'] = 'PieChart'
        res.form['axes_x'] = 'is_staff'
        res = res.form.submit('apply')

    def test_graph_post(self):
        url = reverse('admin:auth_user_changelist')
        res = self.app.get(url, user='sax')
        form = res.forms['changelist-form']
        form['action'] = 'graph_queryset'
        for i in range(0, 11):
            form.set('_selected_action', True, i)
        res = form.submit()
        res.form['graph_type'] = 'PieChart'
        res.form['axes_x'] = 'is_staff'
        res = res.form.submit()
