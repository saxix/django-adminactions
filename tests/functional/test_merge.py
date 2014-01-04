import os.path
from functools import partial
from casper.tests import CasperTestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client
from django_dynamic_fixture import G
from sample_data_utils.utils import sequence
from django_webtest import WebTestMixin
import pytest

list_to_string = lambda q: ','.join(map(str, q))


@pytest.mark.functional
class MergeTest(WebTestMixin, CasperTestCase):
    def setUp(self):
        names = partial(sequence, 'username', cache={})()
        first_names = partial(sequence, 'First', cache={})()
        last_names = partial(sequence, 'Last', cache={})()

        self.client = Client()
        self.user = User.objects.create_superuser('sax', '', '123')
        self.client.login(username=self.user.username, password='123')
        G(User, n=5, username=lambda x: next(names),
          first_name=lambda x: next(first_names),
          last_name=lambda x: next(last_names))

    def test_success(self):
        master = User.objects.get(username='username-0')
        other = User.objects.get(username='username-1')
        ids = list_to_string([master.pk, other.pk])

        url = reverse('admin:auth_user_changelist')
        test_file = os.path.join(os.path.dirname(__file__), 'casper-tests/merge.js')
        assert os.path.exists(test_file)
        self.assertTrue(self.casper(test_file,
                                    url=url,
                                    ids=ids,
                                    master_id=master.pk,
                                    other_id=other.pk,
                                    engine='phantomjs'))

        result = User.objects.get(id=master.pk)
        assert result.username == master.username
        assert result.last_name == other.last_name
        assert result.first_name == other.first_name
        assert not User.objects.filter(pk=other.pk).exists()


    def test_swap(self):
        master = User.objects.get(username='username-0')
        other = User.objects.get(username='username-1')
        ids = list_to_string([master.pk, other.pk])

        url = reverse('admin:auth_user_changelist')
        test_file = os.path.join(os.path.dirname(__file__), 'casper-tests/merge_swap.js')
        self.assertTrue(self.casper(test_file,
                                    url=url,
                                    ids=ids,
                                    master_id=master.pk,
                                    other_id=other.pk,
                                    engine='phantomjs'))

        result = User.objects.get(id=other.pk)
        assert result.username == other.username
        assert result.last_name == master.last_name
        assert result.first_name == master.first_name
        assert not User.objects.filter(pk=master.pk).exists()
