# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import StringIO
import xlrd
import csv
import mock
from django_webtest import WebTest
from django_dynamic_fixture import G
from django.contrib.auth.models import User
from demo.utils import (user_grant_permission, admin_register,
                        CheckSignalsMixin, SelectRowsMixin)

__all__ = ['ExportAsCsvTest', 'ExportAsFixtureTest', 'ExportAsCsvTest', 'ExportDeleteTreeTest',
           'ExportAsXlsTest']


class ExportMixin(object):
    fixtures = ['adminactions', 'demoproject']
    urls = 'demo.urls'

    def setUp(self):
        super(ExportMixin, self).setUp()
        self.user = G(User, username='user', is_staff=True, is_active=True)


class ExportAsFixtureTest(ExportMixin, SelectRowsMixin, CheckSignalsMixin, WebTest):
    sender_model = User
    action_name = 'export_as_fixture'
    _selected_rows = [0, 1, 2]

    def test_no_permission(self):
        with user_grant_permission(self.user, ['auth.change_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            form.set('_selected_action', True, 0)
            res = form.submit().follow()
            assert 'Sorry you do not have rights to execute this action' in res.body

    def test_success(self):
        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            form.set('_selected_action', True, 0)
            form.set('_selected_action', True, 1)
            res = form.submit()
            res.form['use_natural_key'] = True
            res = res.form.submit('apply')
            assert res.json[0]['pk'] == 1

    def test_add_foreign_keys(self):
        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            form.set('_selected_action', True, 0)
            form.set('_selected_action', True, 1)
            res = form.submit()
            res.form['use_natural_key'] = True
            res.form['add_foreign_keys'] = True
            res = res.form.submit('apply')
            assert res.json[0]['pk'] == 1

    def _run_action(self, steps=2):
        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            if steps >= 1:
                form = res.forms['changelist-form']
                form['action'] = self.action_name
                self._select_rows(form)
                res = form.submit()
            if steps >= 2:
                res = res.form.submit('apply')
        return res


class ExportDeleteTreeTest(ExportMixin, SelectRowsMixin, CheckSignalsMixin, WebTest):
    sender_model = User
    action_name = 'export_delete_tree'
    _selected_rows = [0, 1, 2]

    def test_no_permission(self):
        with user_grant_permission(self.user, ['auth.change_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            form.set('_selected_action', True, 0)
            res = form.submit().follow()
            assert 'Sorry you do not have rights to execute this action' in res.body

    def test_success(self):
        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            self._select_rows(form, [0, 1])
            res = form.submit()
            res.form['use_natural_key'] = True
            res = res.form.submit('apply')
            assert res.json[0]['pk'] == 1

    def _run_action(self, steps=2):
        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            if steps >= 1:
                form = res.forms['changelist-form']
                form['action'] = self.action_name
                self._select_rows(form)
                res = form.submit()
            if steps >= 2:
                res = res.form.submit('apply')
        return res

    def test_custom_filename(self):
        """
            if the ModelAdmin has `get_export_as_csv_filename()` use that method to get the
            attachment filename
        """
        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            with admin_register(User) as md:
                with mock.patch.object(md, 'get_export_delete_tree_filename', lambda r, q: 'new.test', create=True):
                    res = res.click('Users')
                    form = res.forms['changelist-form']
                    form['action'] = self.action_name
                    form.set('_selected_action', True, 0)
                    form['select_across'] = 1
                    res = form.submit()
                    res = res.form.submit('apply')
                    self.assertEqual(res.content_disposition, u'attachment;filename="new.test"')


class ExportAsCsvTest(ExportMixin, SelectRowsMixin, CheckSignalsMixin, WebTest):
    sender_model = User
    action_name = 'export_as_csv'
    _selected_rows = [0, 1]

    def test_no_permission(self):
        with user_grant_permission(self.user, ['auth.change_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            form = res.forms['changelist-form']
            form['action'] = 'export_as_csv'
            form.set('_selected_action', True, 0)
            res = form.submit().follow()
            assert 'Sorry you do not have rights to execute this action' in res.body

    def test_success(self):
        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            # form.set('_selected_action', True, 1)
            self._select_rows(form)
            res = form.submit()
            res = res.form.submit('apply')
            io = StringIO.StringIO(res.body)
            csv_reader = csv.reader(io)
            rows = 0
            for c in csv_reader:
                rows += 1
            self.assertEqual(rows, 2)

    def test_custom_filename(self):
        """
            if the ModelAdmin has `get_export_as_csv_filename()` use that method to get the
            attachment filename
        """
        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            with admin_register(User) as md:
                with mock.patch.object(md, 'get_export_as_csv_filename', lambda r, q: 'new.test', create=True):
                    res = res.click('Users')
                    form = res.forms['changelist-form']
                    form['action'] = 'export_as_csv'
                    form.set('_selected_action', True, 0)
                    form['select_across'] = 1
                    res = form.submit()
                    res = res.form.submit('apply')
                    self.assertEqual(res.content_disposition, u'attachment;filename="new.test"')

    def _run_action(self, steps=2):
        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            if steps >= 1:
                form = res.forms['changelist-form']
                form['action'] = self.action_name
                self._select_rows(form)
                res = form.submit()
            if steps >= 2:
                res = res.form.submit('apply')
        return res


class ExportAsXlsTest(ExportMixin, SelectRowsMixin, CheckSignalsMixin, WebTest):
    sender_model = User
    action_name = 'export_as_xls'
    _selected_rows = [0, 1]

    def _run_action(self, step=3):
        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            if step >= 1:
                form = res.forms['changelist-form']
                form['action'] = self.action_name
                self._select_rows(form)
                res = form.submit()
            if step >= 2:
                res.form['header'] = 1
                res = res.form.submit('apply')
            return res

    def test_no_permission(self):
        with user_grant_permission(self.user, ['auth.change_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            form = res.forms['changelist-form']
            form['action'] = 'export_as_xls'
            form.set('_selected_action', True, 0)
            res = form.submit().follow()
            assert 'Sorry you do not have rights to execute this action' in res.body

    def test_success(self):
        with user_grant_permission(self.user, ['auth.change_user', 'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            # form.set('_selected_action', True, 0)
            # form.set('_selected_action', True, 1)
            # form.set('_selected_action', True, 2)
            self._select_rows(form)
            res = form.submit()
            res.form['header'] = 1
            res.form['columns'] = ['id', 'username', 'first_name'
                                                     '']
            res = res.form.submit('apply')
            io = StringIO.StringIO(res.body)

            io.seek(0)
            w = xlrd.open_workbook(file_contents=io.read())
            sheet = w.sheet_by_index(0)
            self.assertEquals(sheet.cell_value(0, 0), u'#')
            self.assertEquals(sheet.cell_value(0, 1), u'ID')
            self.assertEquals(sheet.cell_value(0, 2), u'username')
            self.assertEquals(sheet.cell_value(0, 3), u'first name')
            self.assertEquals(sheet.cell_value(1, 1), 1.0)
            self.assertEquals(sheet.cell_value(1, 2), u'sax')
            self.assertEquals(sheet.cell_value(2, 2), u'user')
            # self.assertEquals(sheet.cell_value(3, 2), u'user_00')

    def test_use_display_ok(self):
        with user_grant_permission(self.user, ['demo.change_demomodel', 'demo.adminactions_export_demomodel']):
            res = self.app.get('/', user='user')
            res = res.click('Demo models')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            self._select_rows(form)
            res = form.submit()
            res.form['header'] = 1
            res.form['use_display'] = 1
            res.form['columns'] = ['char', 'text', 'bigint', 'choices'
                                                             '']
            res = res.form.submit('apply')
            io = StringIO.StringIO(res.body)

            io.seek(0)
            w = xlrd.open_workbook(file_contents=io.read())
            sheet = w.sheet_by_index(0)
            self.assertEquals(sheet.cell_value(0, 1), u'Chäř')
            self.assertEquals(sheet.cell_value(0, 2), u'bigint')
            self.assertEquals(sheet.cell_value(0, 3), u'text')
            self.assertEquals(sheet.cell_value(0, 4), u'choices')
            self.assertEquals(sheet.cell_value(1, 1), u'Pizzä ïs Gööd')
            self.assertEquals(sheet.cell_value(1, 2), 333333333.0)
            self.assertEquals(sheet.cell_value(1, 3), u'lorem ipsum')
            self.assertEquals(sheet.cell_value(1, 4), u'Choice 2')

    def test_use_display_ko(self):
        with user_grant_permission(self.user, ['demo.change_demomodel', 'demo.adminactions_export_demomodel']):
            res = self.app.get('/', user='user')
            res = res.click('Demo models')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            self._select_rows(form)
            res = form.submit()
            res.form['header'] = 1
            res.form['columns'] = ['char', 'text', 'bigint', 'choices'
                                                             '']
            res = res.form.submit('apply')
            io = StringIO.StringIO(res.body)

            io.seek(0)
            w = xlrd.open_workbook(file_contents=io.read())
            sheet = w.sheet_by_index(0)
            self.assertEquals(sheet.cell_value(0, 1), u'Chäř')
            self.assertEquals(sheet.cell_value(0, 2), u'bigint')
            self.assertEquals(sheet.cell_value(0, 3), u'text')
            self.assertEquals(sheet.cell_value(0, 4), u'choices')
            self.assertEquals(sheet.cell_value(1, 1), u'Pizzä ïs Gööd')
            self.assertEquals(sheet.cell_value(1, 2), 333333333.0)
            self.assertEquals(sheet.cell_value(1, 3), u'lorem ipsum')
            self.assertEquals(sheet.cell_value(1, 4), 2.0)

    def test_unicode(self):
       with user_grant_permission(self.user, ['demo.change_demomodel', 'demo.adminactions_export_demomodel']):
            res = self.app.get('/', user='user')
            res = res.click('Demo models')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            self._select_rows(form)
            res = form.submit()
            res.form['header'] = 1
            res.form['columns'] = ['char',]
            res = res.form.submit('apply')
            io = StringIO.StringIO(res.body)

            io.seek(0)
            w = xlrd.open_workbook(file_contents=io.read())
            sheet = w.sheet_by_index(0)
            self.assertEquals(sheet.cell_value(0, 1), u'Chäř')
            self.assertEquals(sheet.cell_value(1, 1), u'Pizzä ïs Gööd')
