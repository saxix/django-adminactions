from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import G
from django_webtest import WebTestMixin
from utils import CheckSignalsMixin, SelectRowsMixin, user_grant_permission

from demo.models import DemoModel

__all__ = ['MassUpdateTest', ]


class MassUpdateTest(SelectRowsMixin, CheckSignalsMixin, WebTestMixin, TestCase):
    fixtures = ['adminactions', 'demoproject']
    urls = 'demo.urls'
    csrf_checks = True

    _selected_rows = [0, 1]

    action_name = 'mass_update'
    sender_model = DemoModel

    def setUp(self):
        super(MassUpdateTest, self).setUp()
        self._url = reverse('admin:demo_demomodel_changelist')
        self.user = G(User, username='user', is_staff=True, is_active=True)

    def _run_action(self, steps=2, **kwargs):
        selected_rows = kwargs.pop('selected_rows', self._selected_rows)
        with user_grant_permission(self.user, ['demo.change_demomodel',
                                               'demo.adminactions_massupdate_demomodel']):
            res = self.app.get('/', user='user')
            res = res.click('Demo models')
            if steps >= 1:
                form = res.forms['changelist-form']
                form['action'] = 'mass_update'
                self._select_rows(form, selected_rows)
                res = form.submit()
            if steps >= 2:
                for k, v in kwargs.items():
                    res.form[k] = v
                res.form['chk_id_char'].checked = True
                res.form['func_id_char'] = 'upper'
                res.form['chk_id_choices'].checked = True
                res.form['func_id_choices'] = 'set'
                res.form['choices'] = '1'
                res = res.form.submit('apply')
        return res

    def test_no_permission(self):
        with user_grant_permission(self.user, ['demo.change_demomodel']):
            res = self.app.get('/', user='user')
            res = res.click('Demo models')
            form = res.forms['changelist-form']
            form['action'] = 'mass_update'
            form.set('_selected_action', True, 0)
            res = form.submit().follow()
            assert 'Sorry you do not have rights to execute this action' in str(res.body)

    def test_validate_on(self):
        self._run_action(**{'_validate': 1})
        assert DemoModel.objects.filter(char='CCCCC').exists()
        assert not DemoModel.objects.filter(char='ccccc').exists()

    def test_validate_off(self):
        self._run_action(**{'_validate': 0})
        self.assertIn("Unable no mass update using operators without", self.app.cookies['messages'])

    def test_clean_on(self):
        self._run_action(**{'_clean': 1})

        assert DemoModel.objects.filter(char='CCCCC').exists()
        assert not DemoModel.objects.filter(char='ccccc').exists()

    def test_messages(self):
        with user_grant_permission(self.user, ['demo.change_demomodel', 'demo.adminactions_massupdate_demomodel']):
            res = self._run_action(**{'_clean': 1}).follow()
            messages = [m.message for m in list(res.context['messages'])]
            self.assertTrue(messages)
            self.assertEqual('Updated 2 records', messages[0])

            res = self._run_action(selected_rows=[1]).follow()
            messages = [m.message for m in list(res.context['messages'])]
            self.assertTrue(messages)
            self.assertEqual('Updated 1 records', messages[0])
