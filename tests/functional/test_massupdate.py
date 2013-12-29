import os.path
from casper.tests import CasperTestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client
from django_dynamic_fixture import G
from django_webtest import WebTestMixin

list_to_string = lambda q: ','.join(map(str, q))


class MassUpdateTest(WebTestMixin, CasperTestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser('sax', '', '123')
        self.client.login(username=self.user.username, password='123')

        G(User, n=5)

    def test_success(self):
        new_first_name = '**FIRST_NAME**'
        new_last_name = '**LAST_NAME**'

        selection = User.objects.filter(is_superuser=False)
        ids = list_to_string(selection.values_list('pk', flat=True))


        url = reverse('admin:auth_user_changelist')
        test_file = os.path.join(os.path.dirname(__file__), 'casper-tests/massupdate_success.js')
        self.assertTrue(self.casper(test_file,
                                    url=url,
                                    first_name=new_first_name,
                                    last_name=new_last_name,
                                    ids=ids,
                                    engine='phantomjs'))


        result = User.objects.filter(last_name=new_last_name,
                                     first_name=new_first_name)

        self.assertEquals(result.count(), selection.count())

    def test_check_clean(self):
        new_first_name = '**FIRST_NAME**'
        new_last_name = '**LAST_NAME**'

        selection = User.objects.filter(is_superuser=False)
        ids = list_to_string(selection.values_list('pk', flat=True))


        url = reverse('admin:auth_user_changelist')
        test_file = os.path.join(os.path.dirname(__file__), 'casper-tests/massupdate_clean.js')
        self.assertTrue(self.casper(test_file,
                                    url=url,
                                    first_name=new_first_name,
                                    last_name=new_last_name,
                                    ids=ids,
                                    engine='phantomjs'))


        result = User.objects.filter(last_name=new_last_name,
                                     first_name=new_first_name)

        self.assertEquals(result.count(), selection.count())
