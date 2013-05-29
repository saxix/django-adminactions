# -*- encoding: utf-8 -*-
import StringIO
import csv
import mock
import django.contrib.admin
from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.forms import Form
from adminactions.tests.common import BaseTestCase
from adminactions.exceptions import ActionInterrupted
from adminactions.signals import adminaction_requested, adminaction_start, adminaction_end


__all__ = ['ExportAsCsvTest', 'ExportAsFixtureTest', 'ExportAsCsvTest', 'ExportDeleteTreeTest']


class CheckSignalsMixin(object):
    def test_signal_requested(self):
        # test if adminaction_requested Signal can stop the action

        MESSAGE = 'Action Interrupted Test'

        def myhandler(sender, action, request, queryset, **kwargs):
            myhandler.invoked = True
            self.assertEqual(action, self.action_name)
            self.assertSequenceEqual(queryset.order_by('id').values_list('id', flat=True), self.selected_rows)
            raise ActionInterrupted(MESSAGE)

        try:
            adminaction_requested.connect(myhandler, sender=Permission)
            response = self._run_action(code2=302)
            self.assertTrue(myhandler.invoked)
            self.assertIn(MESSAGE, response.cookies['messages'].value)
        finally:
            adminaction_requested.disconnect(myhandler, sender=Permission)

    def test_signal_start(self):
        # test if adminaction_start Signal can stop the action

        MESSAGE = 'Action Interrupted Test'
        SELECTION = [2, 3, 4]

        def myhandler(sender, action, request, queryset, form, **kwargs):
            myhandler.invoked = True
            self.assertEqual(action, self.action_name)
            self.assertSequenceEqual(queryset.order_by('id').values_list('id', flat=True), SELECTION)
            self.assertTrue(isinstance(form, Form))
            raise ActionInterrupted(MESSAGE)

        try:
            adminaction_start.connect(myhandler, sender=Permission)
            response = self._run_action(code3=302)
            self.assertTrue(myhandler.invoked)
            self.assertIn(MESSAGE, response.cookies['messages'].value)
        finally:
            adminaction_start.disconnect(myhandler, sender=Permission)

    def test_signal_end(self):
        # test if adminaction_start Signal can stop the action

        SELECTION = [2, 3, 4]

        def myhandler(sender, action, request, queryset, **kwargs):
            myhandler.invoked = True
            self.assertEqual(action, self.action_name)
            self.assertSequenceEqual(queryset.order_by('id').values_list('id', flat=True), SELECTION)

        try:
            adminaction_end.connect(myhandler, sender=Permission)
            self._run_action(code3=200)
            self.assertTrue(myhandler.invoked)
        finally:
            adminaction_end.disconnect(myhandler, sender=Permission)


class ExecuteActionMixin(object):
    def _run_action(self, code1=200, code2=200, code3=200, **kwargs):
        kwargs.setdefault('select_across', 0)
        kwargs.setdefault('_selected_action', self.selected_rows)
        kwargs.setdefault('index', 0)
        kwargs.setdefault('action', self.action_name)

        url = kwargs.pop('url', self._url)

        response = self.client.get(url)
        self.assertEqual(response.status_code, code1)
        response = self.client.post(url, kwargs)
        self.assertEqual(response.status_code, code2)
        #post the form
        if code2 == 200:
            data = response.context['adminform'].form.initial
            data.update({'apply': 'Export'})
            response = self.client.post(url, data)

            self.assertEqual(response.status_code, code3)
        return response


class BaseExportTest(BaseTestCase, ExecuteActionMixin):
    def setUp(self):
        super(BaseExportTest, self).setUp()
        self._url = reverse('admin:auth_permission_changelist')
        self.original_verbose_name = Permission._meta.verbose_name_plural

    def tearDown(self):
        super(BaseExportTest, self).tearDown()
        Permission._meta.verbose_name_plural = self.original_verbose_name

    def test_custom_filename(self):
        md = django.contrib.admin.site._registry[Permission]
        with mock.patch.object(md, 'get_%s_filename' % self.action_name, lambda r, q: 'new.test', create=True):
            response = self._run_action(select_across=1)
            self.assertEqual(response['Content-Disposition'], u'attachment;filename="new.test"')

    def test_unicode(self):
        Permission._meta.verbose_name_plural = u'replaced_ë'
        response = self._run_action(select_across=1)
        self.assertAlmostEqual(response['Content-Disposition'], 'attachment;filename="replaced_?.%s"' % self.suffix)

    def test_happy_path(self):
        url = reverse('admin:auth_user_changelist')

        def myhandler(sender, action, request, queryset, **kwargs):
            self.assertEqual(action, self.action_name)
            self.assertSequenceEqual(queryset.order_by('id').values_list('id', flat=True), self.selected_rows)

        try:
            adminaction_start.connect(myhandler, sender=User)
            adminaction_end.connect(myhandler, sender=User)
            adminaction_requested.connect(myhandler, sender=User)
            response = self._run_action(url=url, header=1)
            self.assertIn('Content-Disposition', response)
            self.assertIn('attachment;filename=', response['Content-Disposition'])
        finally:
            adminaction_start.disconnect(myhandler, sender=User)
            adminaction_end.disconnect(myhandler, sender=User)
            adminaction_requested.disconnect(myhandler, sender=User)


class ExportAsCsvTest(BaseExportTest, CheckSignalsMixin):
    urls = "adminactions.tests.urls"
    action_name = 'export_as_csv'
    selected_rows = [2, 3, 4]
    suffix = 'csv'

    def setUp(self):
        super(ExportAsCsvTest, self).setUp()
        self._url = reverse('admin:auth_permission_changelist')

    def test_permission(self):
        # test if right permission is checked
        self.login('user_0', '123')  # normal user
        self.add_permission('auth.change_permission')
        response = self._run_action(code2=302)
        self.assertIn("Sorry you do not have rights to execute this action", response.cookies['messages'].value)

    def test_export_across(self):
        response = self._run_action(select_across=1)
        self.assertEqual(response['Content-Disposition'], 'attachment;filename="permissions.csv"')
        self.assertEqual(response.status_code, 200)

        io = StringIO.StringIO(response.content)
        csv_reader = csv.reader(io)
        rows = 0
        for c in csv_reader:
            rows += 1
        self.assertEqual(rows, Permission.objects.count())
        self.assertEqual(response.status_code, 200)

    def test_selected_row(self):
        response = self._run_action()
        io = StringIO.StringIO(response.content)
        csv_reader = csv.reader(io)
        rows = 0
        for c in csv_reader:
            rows += 1
        self.assertEqual(rows, 3)
        self.assertEqual(response.status_code, 200)


class ExportAsFixtureTest(BaseExportTest, CheckSignalsMixin):
    urls = "adminactions.tests.urls"
    action_name = 'export_as_fixture'
    selected_rows = [2, 3, 4]
    suffix = 'json'

    def setUp(self):
        super(ExportAsFixtureTest, self).setUp()
        self._url = reverse('admin:auth_permission_changelist')

    def test_permission(self):
        # test if right permission is checked
        self.login('user_0', '123')  # normal user
        self.add_permission('auth.change_permission')
        response = self._run_action(code2=302)
        self.assertIn("Sorry you do not have rights to execute this action", response.cookies['messages'].value)


class ExportDeleteTreeTest(BaseExportTest, CheckSignalsMixin):
    urls = "adminactions.tests.urls"
    action_name = 'export_delete_tree'
    selected_rows = [2, 3, 4]
    suffix = 'json'

    def setUp(self):
        super(ExportDeleteTreeTest, self).setUp()
        self._url = reverse('admin:auth_permission_changelist')

    def test_permission(self):
        # test if right permission is checked
        self.login('user_0', '123')  # normal user
        self.add_permission('auth.change_permission')
        response = self._run_action(code2=302)
        self.assertIn("Sorry you do not have rights to execute this action", response.cookies['messages'].value)
