from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django_dynamic_fixture import G
from django_webtest import WebTestMixin
from utils import SelectRowsMixin, user_grant_permission

from adminactions.byrows_update import byrows_update_get_fields
from demo.models import DemoModel


class MockRequest:
    pass


class TestByRowsUpdateAction(WebTestMixin, SelectRowsMixin, TestCase):
    fixtures = ['adminactions', 'demoproject']
    urls = 'demo.urls'
    action_name = 'byrows_update'
    sender_model = DemoModel
    _selected_rows = [0, 1]
    csrf_checks = False

    def setUp(self):
        super().setUp()
        self._url = reverse('admin:demo_demomodel_changelist')
        self.user = G(User, username='user', is_staff=True, is_active=True)
        self.site = AdminSite()
        self.mockRequest = MockRequest()

    def _get_changelist_form_response(self):
        res = self.app.get('/', user='user')
        res = res.click('Demo models')
        return res

    def _get_action_form_response(self, change_list_response=None):
        form = change_list_response.forms['changelist-form']
        form['action'] = 'byrows_update'
        res = form.submit()
        return res

    def test_no_permission(self):
        with user_grant_permission(self.user, ['demo.change_demomodel']):
            res = self._get_changelist_form_response()

            form = res.forms['changelist-form']
            form['action'] = 'byrows_update'
            self._select_rows(form, selected_rows=self._selected_rows)
            res = form.submit().follow()
            assert 'Sorry you do not have rights to execute this action' in str(res.body)

    def test_form_rows_count(self):
        """
            Count the selected items appear in the action form
        """
        self.renew_app()
        with user_grant_permission(self.user, ['demo.change_demomodel',
                                               'demo.adminactions_byrowsupdate_demomodel']):
            res = self._get_changelist_form_response()

            form = res.forms['changelist-form']
            self._select_rows(form, selected_rows=self._selected_rows)
            res = self._get_action_form_response(change_list_response=res)
            self.assertEqual(len(res.html.find(id="formset").find_all(class_="row")), len(self._selected_rows))

    def test_form_rows_fields_exists(self):
        """
            Check model fields appear in action form for each selected models
        """
        with user_grant_permission(self.user, ['demo.change_demomodel', 'demo.adminactions_byrowsupdate_demomodel']):
            res = self._get_changelist_form_response()

            form = res.forms['changelist-form']
            self._select_rows(form, selected_rows=self._selected_rows)
            res = self._get_action_form_response(change_list_response=res)
            byrows_update_get_fields(ModelAdmin(DemoModel, self.site))
            for r, value in enumerate(self._selected_values):
                for fname in byrows_update_get_fields(ModelAdmin(DemoModel, self.site)):
                    fname = 'form-%d-%s' % (r, fname)

                    try:
                        # Attempt split (admin datetime widget) fields first
                        assert res.form[fname + '_0']
                    except AssertionError:
                        # assert for non-split fields to return the regular
                        # field name upon errors
                        assert res.form[fname]

    def test_form_rows_edit(self):
        """
            Modify a value in action form and see if its stored upon form submit
        """
        with user_grant_permission(self.user, ['demo.change_demomodel', 'demo.adminactions_byrowsupdate_demomodel']):
            res = self._get_changelist_form_response()

            form = res.forms['changelist-form']
            self._select_rows(form, selected_rows=self._selected_rows)
            res = self._get_action_form_response(change_list_response=res)

            row_to_modify = 0
            new_values = {
                'char': 'Bob Marley'
            }
            for k, v in new_values.items():
                res.form["form-%d-%s" % (row_to_modify, k)] = v
            res.form.submit('apply')
            obj = DemoModel.objects.get(id=self._selected_values[row_to_modify])
            for k, v in new_values.items():
                self.assertEqual(v, getattr(obj, k))
