# -*- encoding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import io
import six
import time
import unittest

import mock
import xlrd
from django.contrib.auth.models import User
from django.test.utils import override_settings
from django.utils.encoding import smart_text
from django_dynamic_fixture import G
from django_webtest import WebTest
from utils import (CheckSignalsMixin, SelectRowsMixin, admin_register,
                   user_grant_permission,)

if six.PY2:
    import unicodecsv as csv
else:
    import csv

__all__ = ['ExportAsCsvTest', 'ExportAsFixtureTest', 'ExportAsCsvTest',
           'ExportDeleteTreeTest', 'ExportAsXlsTest']


class ExportMixin(object):
    fixtures = ['adminactions', 'demoproject']
    urls = 'demo.urls'
    csrf_checks = True

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
            assert six.b(
                'Sorry you do not have rights to execute this action') in res.body

    def test_success(self):
        with user_grant_permission(self.user, ['auth.change_user',
                                               'auth.adminactions_export_user']):
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
        with user_grant_permission(self.user, ['auth.change_user',
                                               'auth.adminactions_export_user']):
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
        with user_grant_permission(self.user, ['auth.change_user',
                                               'auth.adminactions_export_user']):
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
            assert six.b(
                'Sorry you do not have rights to execute this action') in res.body

    def test_success(self):
        with user_grant_permission(self.user, ['auth.change_user',
                                               'auth.adminactions_export_user']):
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
        with user_grant_permission(self.user, ['auth.change_user',
                                               'auth.adminactions_export_user']):
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
            if the ModelAdmin has `get_export_as_csv_filename()`
            use that method to get the attachment filename
        """
        with user_grant_permission(self.user, ['auth.change_user',
                                               'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            with admin_register(User) as md:
                with mock.patch.object(md, 'get_export_delete_tree_filename',
                                       lambda r, q: 'new.test', create=True):
                    res = res.click('Users')
                    form = res.forms['changelist-form']
                    form['action'] = self.action_name
                    form.set('_selected_action', True, 0)
                    form['select_across'] = 1
                    res = form.submit()
                    res = res.form.submit('apply')
                    self.assertEqual(res.content_disposition,
                                     'attachment;filename="new.test"')


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
            assert six.b(
                'Sorry you do not have rights to execute this action') in res.body

    def test_success(self):
        with user_grant_permission(self.user, ['demo.change_demomodel',
                                               'demo.adminactions_export_demomodel']):
            res = self.app.get('/', user='user')
            res = res.click('Demo models')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            # form.set('_selected_action', True, 1)
            self._select_rows(form)
            res = form.submit()
            res = res.form.submit('apply')
            if six.PY2:
                buff = io.BytesIO(res.body)
            else:
                buff = io.StringIO(smart_text(res.body))
            csv_reader = csv.reader(buff)

            self.assertEqual(len(list(csv_reader)), 2)

    def test_custom_filename(self):
        """
            if the ModelAdmin has `get_export_as_csv_filename()` use that method to get the
            attachment filename
        """
        with user_grant_permission(self.user, ['auth.change_user',
                                               'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            with admin_register(User) as md:
                with mock.patch.object(md, 'get_export_as_csv_filename',
                                       lambda r, q: 'new.test', create=True):
                    res = res.click('Users')
                    form = res.forms['changelist-form']
                    form['action'] = 'export_as_csv'
                    form.set('_selected_action', True, 0)
                    form['select_across'] = 1
                    res = form.submit()
                    res = res.form.submit('apply')
                    self.assertEqual(res.content_disposition,
                                     u'attachment;filename="new.test"')

    def _run_action(self, steps=2):
        with user_grant_permission(self.user, ['auth.change_user',
                                               'auth.adminactions_export_user']):
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

    @override_settings(ADMINACTIONS_STREAM_CSV=True)
    def test_streaming_export(self):
        res = self._run_action()
        if six.PY2:
            buff = io.BytesIO(res.body)
        else:
            buff = io.StringIO(smart_text(res.body))
        csv_reader = csv.reader(buff)

        self.assertEqual(len(list(csv_reader)), 2)


class ExportAsXlsTest(ExportMixin, SelectRowsMixin, CheckSignalsMixin, WebTest):
    sender_model = User
    action_name = 'export_as_xls'
    _selected_rows = [0, 1]

    def _run_action(self, step=3):
        with user_grant_permission(self.user, ['auth.change_user',
                                               'auth.adminactions_export_user']):
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
            assert six.b(
                'Sorry you do not have rights to execute this action') in res.body

    def test_success(self):
        with user_grant_permission(self.user, ['auth.change_user',
                                               'auth.adminactions_export_user']):
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
            io = six.BytesIO(res.body)

            io.seek(0)
            w = xlrd.open_workbook(file_contents=io.read())
            sheet = w.sheet_by_index(0)
            self.assertEqual(sheet.cell_value(0, 0), u'#')
            self.assertEqual(sheet.cell_value(0, 1), u'ID')
            self.assertEqual(sheet.cell_value(0, 2), u'username')
            self.assertEqual(sheet.cell_value(0, 3), u'first name')
            self.assertEqual(sheet.cell_value(1, 1), 1.0)
            self.assertEqual(sheet.cell_value(1, 2), u'sax')
            self.assertEqual(sheet.cell_value(2, 2), u'user')
            # self.assertEqual(sheet.cell_value(3, 2), u'user_00')

    def test_use_display_ok(self):
        with user_grant_permission(self.user, ['demo.change_demomodel',
                                               'demo.adminactions_export_demomodel']):
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
            io = six.BytesIO(res.body)

            io.seek(0)
            w = xlrd.open_workbook(file_contents=io.read())
            sheet = w.sheet_by_index(0)
            self.assertEqual(sheet.cell_value(0, 1), u'Chäř')
            self.assertEqual(sheet.cell_value(0, 2), u'bigint')
            self.assertEqual(sheet.cell_value(0, 3), u'text')
            self.assertEqual(sheet.cell_value(0, 4), u'choices')
            self.assertEqual(sheet.cell_value(1, 1), u'Pizzä ïs Gööd')
            self.assertEqual(sheet.cell_value(1, 2), 333333333.0)
            self.assertEqual(sheet.cell_value(1, 3), u'lorem ipsum')
            self.assertEqual(sheet.cell_value(1, 4), u'Choice 2')

    def test_use_display_ko(self):
        with user_grant_permission(self.user, ['demo.change_demomodel',
                                               'demo.adminactions_export_demomodel']):
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
            io = six.BytesIO(res.body)

            io.seek(0)
            w = xlrd.open_workbook(file_contents=io.read())
            sheet = w.sheet_by_index(0)
            self.assertEqual(sheet.cell_value(0, 1), u'Chäř')
            self.assertEqual(sheet.cell_value(0, 2), u'bigint')
            self.assertEqual(sheet.cell_value(0, 3), u'text')
            self.assertEqual(sheet.cell_value(0, 4), u'choices')
            self.assertEqual(sheet.cell_value(1, 1), u'Pizzä ïs Gööd')
            self.assertEqual(sheet.cell_value(1, 2), 333333333.0)
            self.assertEqual(sheet.cell_value(1, 3), u'lorem ipsum')
            self.assertEqual(sheet.cell_value(1, 4), 2.0)

    def test_unicode(self):
        with user_grant_permission(self.user, ['demo.change_demomodel',
                                               'demo.adminactions_export_demomodel']):
            res = self.app.get('/', user='user')
            res = res.click('Demo models')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            self._select_rows(form)
            res = form.submit()
            res.form['header'] = 1
            res.form['columns'] = ['char', ]
            res = res.form.submit('apply')
            io = six.BytesIO(res.body)

            io.seek(0)
            w = xlrd.open_workbook(file_contents=io.read())
            sheet = w.sheet_by_index(0)
            self.assertEqual(sheet.cell_value(0, 1), u'Chäř')
            self.assertEqual(sheet.cell_value(1, 1), u'Pizzä ïs Gööd')

    def test_issue_93(self):
        # default date(time) format in XLS export doesn't import well on excel
        with user_grant_permission(self.user, ['demo.change_demomodel',
                                               'demo.adminactions_export_demomodel']):
            res = self.app.get('/', user='user')
            res = res.click('Demo models')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            self._select_rows(form)
            res = form.submit()
            res.form['header'] = 1
            res.form['columns'] = ['date', ]
            res = res.form.submit('apply')
            io = six.BytesIO(res.body)

            io.seek(0)
            w = xlrd.open_workbook(file_contents=io.read(), formatting_info=True)
            sheet = w.sheet_by_index(0)

            cell = sheet.cell(1, 1)
            fmt = w.xf_list[cell.xf_index]
            format_key = fmt.format_key
            format = w.format_map[format_key]  # gets a Format object

            self.assertEqual(cell.value, 41303.0)
            self.assertEqual(cell.ctype, 3)
            self.assertEqual(format.format_str, u'd/m/Y')

    @unittest.skip("Impossible to reliably time different machine runs")
    def test_faster_export(self):
        # generate 3k users
        start = time.time()
        user_count = User.objects.count()
        User.objects.bulk_create([User(
            username='bulk_user_%s' % i) for i in range(3000)])
        # print('created 3k users in %.1f seconds' % (time.time() - start))
        self.assertEqual(User.objects.count(), 3000 + user_count)

        start = time.time()
        with user_grant_permission(self.user, [
                'auth.change_user', 'auth.adminactions_export_user']):
            res = self.app.get('/', user='user')
            res = res.click('Users')
            form = res.forms['changelist-form']
            form['action'] = self.action_name
            form['select_across'] = 1
            self._select_rows(form)
            res = form.submit()
            res.form['header'] = 1
            res = res.form.submit('apply')

        res_time = (time.time() - start)
        # print('Response returned in %.1f seconds' % res_time)

        io = six.BytesIO(res.body)

        io.seek(0)
        w = xlrd.open_workbook(file_contents=io.read())
        sheet = w.sheet_by_index(0)

        self.assertEqual(sheet.nrows, 3000 + user_count + 1)
        self.assertLessEqual(res_time, 6.5, "Response should return under 6.5 "
                             "seconds, was %.2f" % res_time)
