from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_dynamic_fixture import G
from django_webtest import WebTestMixin
from django.test import TestCase, TransactionTestCase
from webtests.utils import CheckSignalsMixin, user_grant_permission, SelectRowsMixin


__all__ = ['MassUpdateTest', ]


class MassUpdateTest(SelectRowsMixin, CheckSignalsMixin, WebTestMixin, TransactionTestCase):
    fixtures = ['adminactions', 'demoproject']
    urls = 'demoproject.urls'

    _selected_rows = [1, 2, 3, 4]

    action_name = 'mass_update'
    sender_model = User

    def setUp(self):
        super(MassUpdateTest, self).setUp()
        self._url = reverse('admin:auth_user_changelist')
        self.user = G(User, username='user', is_staff=True, is_active=True)


    def _run_action(self, steps=2, **kwargs):
        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_massupdate_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            if steps >= 1:
                form = res.forms['changelist-form']
                form['action'] = 'mass_update'
                self._select_rows(form)
                res = form.submit()
            if steps >= 2:
                for k, v in kwargs.items():
                    res.form[k] = v
                res.form['chk_id_username'].checked = True
                res.form['chk_id_last_name'].checked = True
                res.form['func_id_username'] = 'upper'
                res.form['func_id_last_name'] = 'set'
                res.form['last_name'] = 'LASTNAME'
                res = res.form.submit('apply')
        return res

    def test_no_permission(self):
        with user_grant_permission(self.user, ['auth.change_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            form = res.forms['changelist-form']
            form['action'] = 'mass_update'
            form.set('_selected_action', True, 0)
            res = form.submit().follow()
            assert 'Sorry you do not have rights to execute this action' in res.body

    def test_validate_on(self):
        res = self._run_action(**{'_validate': 1})
        assert User.objects.filter(username='USER').exists()
        assert not User.objects.filter(username='user').exists()
        assert User.objects.filter(last_name='LASTNAME').count() == len(self._selected_rows)

    def test_validate_off(self):
        res = self._run_action(**{'_validate': 0})
        self.assertIn("Unable no mass update using operators without",  self.app.cookies['messages'])
        #assert "Unable no mass update using operators without" in res.body

    def test_clean_on(self):
        res = self._run_action(**{'_clean': 1})
        assert User.objects.filter(username='USER').exists()
        assert not User.objects.filter(username='user').exists()
        assert User.objects.filter(last_name='LASTNAME').count() == len(self._selected_rows)

    def test_unique_transaction(self):
        res = self._run_action(**{'_unique_transaction': 1})
        assert User.objects.filter(username='USER').exists()
        assert not User.objects.filter(username='user').exists()
        assert User.objects.filter(last_name='LASTNAME').count() == len(self._selected_rows)
