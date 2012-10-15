import StringIO
import csv
from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from adminactions.tests.common import BaseTestCase


__all__ = ['MassUpdateTest', ]


class ExportAsCsvTest(BaseTestCase):
    urls = "adminactions.tests.urls"

    def setUp(self):
        super(ExportAsCsvTest, self).setUp()
        self._url = reverse('admin:auth_permission_changelist')

    def test_export_across(self):
        response = self.client.get(self._url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self._url, {'action': 'export_as_csv',
                                                'index': 0,
                                                'select_across': 1,
                                                '_selected_action': [2, 3, 4]})
        self.assertEqual(response.status_code, 200)
        data = response.context['form'].initial
        data.update({'apply': 'Export'})
        response = self.client.post(self._url, data)

        io = StringIO.StringIO(response.content)
        csv_reader = csv.reader(io)
        rows = 0
        for c in csv_reader:
            rows += 1
        self.assertEqual(rows, Permission.objects.count())
        self.assertEqual(response.status_code, 200)

    def test_selected_row(self):
        response = self.client.post(self._url, {'action': 'export_as_csv',
                                                'index': 0,
                                                'select_across': 0,
                                                '_selected_action': [2, 3, 4]})
        data = response.context['form'].initial
        data.update({'apply': 'Export'})
        response = self.client.post(self._url, data)

        io = StringIO.StringIO(response.content)
        csv_reader = csv.reader(io)
        rows = 0
        for c in csv_reader:
            rows += 1
        self.assertEqual(rows, 3)
        self.assertEqual(response.status_code, 200)

