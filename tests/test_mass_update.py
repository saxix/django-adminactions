from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G
from django_webtest import WebTestMixin
from django.test import TransactionTestCase
from tests.models import DemoModel
from .utils import CheckSignalsMixin, user_grant_permission, SelectRowsMixin


__all__ = ['MassUpdateTest', ]


class MassUpdateTest(SelectRowsMixin, CheckSignalsMixin, WebTestMixin, TransactionTestCase):
    fixtures = ['adminactions', 'demoproject']
    urls = 'tests.urls'

    _selected_rows = [0, 1]

    action_name = 'mass_update'
    sender_model = DemoModel

    def setUp(self):
        super(MassUpdateTest, self).setUp()
        self._url = reverse('admin:tests_demomodel_changelist')
        self.user = G(User, username='user', is_staff=True, is_active=True)

    def _run_action(self, steps=2, **kwargs):
        with user_grant_permission(self.user, ['tests.change_demomodel', 'tests.adminactions_massupdate_demomodel']):
            res = self.app.get('/', user='user')
            res = res.click('Demo models')
            if steps >= 1:
                form = res.forms['changelist-form']
                form['action'] = 'mass_update'
                self._select_rows(form)
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
        with user_grant_permission(self.user, ['tests.change_demomodel']):
            res = self.app.get('/', user='user')
            res = res.click('Demo models')
            form = res.forms['changelist-form']
            form['action'] = 'mass_update'
            form.set('_selected_action', True, 0)
            res = form.submit().follow()
            assert 'Sorry you do not have rights to execute this action' in res.body

    def test_validate_on(self):
        self._run_action(**{'_validate': 1})
        assert DemoModel.objects.filter(char='BBB').exists()
        assert not DemoModel.objects.filter(char='bbb').exists()
        # assert DemoModel.objects.filter(last_name='LASTNAME').count() == len(self._selected_rows)

    def test_validate_off(self):
        self._run_action(**{'_validate': 0})
        self.assertIn("Unable no mass update using operators without", self.app.cookies['messages'])
        # assert "Unable no mass update using operators without" in res.body

    def test_clean_on(self):
        self._run_action(**{'_clean': 1})
        assert DemoModel.objects.filter(char='BBB').exists()
        assert not DemoModel.objects.filter(char='bbb').exists()
        # assert DemoModel.objects.filter(last_name='LASTNAME').count() == len(self._selected_rows)

    def test_unique_transaction(self):
        self._run_action(**{'_unique_transaction': 1})
        assert DemoModel.objects.filter(char='BBB').exists()
        assert not DemoModel.objects.filter(char='bbb').exists()
        # assert DemoModel.objects.filter(last_name='LASTNAME').count() == len(self._selected_rows)
