from django.contrib import auth
from django.contrib.auth.models import User
from django.core.handlers.base import BaseHandler
from django.core.urlresolvers import reverse
from django.contrib.admin.sites import site
from django.test.client import RequestFactory
from adminactions.tests.common import BaseTestCase

__all__ = ['MassUpdateTest', ]


class MiddlewareRequestFactory(RequestFactory):
    def request(self, **request):
        request = super(MiddlewareRequestFactory, self).request(**request)
        handler = BaseHandler()
        handler.load_middleware()
        for middleware_method in handler._request_middleware:
            if middleware_method(request):
                raise Exception("Couldn't create request object - "
                                "request middleware returned a response")

        return request


class MassUpdateTest(BaseTestCase):
    def setUp(self):
        super(MassUpdateTest, self).setUp()
        self._url = reverse('admin:auth_user_changelist')

    def test_action_get(self):
        response = self.client.get(self._url, {'action': 'mass_update',
                                               'index': 0,
                                               'select_across': 0,
                                               '_selected_action': [2, 3, 4]})
        self.assertEqual(response.status_code, 302)
        self.assertIn( 'auth/user/?e=1', response['Location'])

    def test_action_post(self):
        target_ids = [2, 3, 4, 7, 10]
        response = self.client.post(self._url, {'action': 'mass_update',
                                                'apply': 'Update records',
                                                'chk_id_is_active': 'on',
                                                '_selected_action': target_ids},
            follow=False)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(target_ids, [u.pk for u in User.objects.filter(is_active=False)])

    def test_many_to_many(self):
        target_ids = [2, 4, 10]
        response = self.client.post(self._url, {'action': 'mass_update',
                                                'apply': 'Update records',
                                                'chk_id_groups': 'on',
                                                'groups': ['2'],
                                                '_validate': 'on',
                                                '_selected_action': target_ids},
            follow=False)
        self.assertEquals(response.status_code, 302)
        updated = User.objects.filter(groups__pk=2).order_by('pk').values_list('pk', flat=True)
        self.assertSequenceEqual(target_ids, updated)
