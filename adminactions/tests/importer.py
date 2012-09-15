from django.core.urlresolvers import reverse
import os
from adminactions.tests.common import BaseTestCase

__all__ = ['CSVImportTest', ]

DATADIR = os.path.join(os.path.dirname(__file__), 'data')


class CSVImportTest(BaseTestCase):
    def dis_test_step_1(self):
        response = self.client.get('/admin/')
        url = reverse('iadmin:import', kwargs=dict(app_label='auth', model_name='user', page=1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Import CSV File" in response.context['title'])

    def dis_test_step_2(self):
        """ load and parese csv file
        """
        f = open(os.path.join(DATADIR, 'user_with_headers.csv'), 'rb')
        url = reverse('iadmin:import', kwargs=dict(app_label='auth', model_name='user', page=2))
        self.client.get(url)
        data = {'model': 'auth:user',
                'csv': f,
                'page': 1,
                }
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)

#    def test_import_csv_without_headers(self):
#        f = open(os.path.join(DATADIR, 'user_with_headers.csv'), 'rb')
#        url = reverse('iadmin:import', kwargs=dict(app_label='auth', model_name='user', page=1))
#        self.client.get(url)
#        data = {'model': 'auth:user',
#                'csv' : f,
#                'page': 1,
#        }
#        response = self.client.get(url, data)
#        self.assertEqual(response.status_code, 200)
