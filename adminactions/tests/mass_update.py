from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from adminactions.tests.common import BaseTestCase


__all__ = ['MassUpdateTest', ]


class MassUpdateTest(BaseTestCase):
    urls = "adminactions.tests.urls"

    def setUp(self):
        super(MassUpdateTest, self).setUp()
        self._url = reverse('admin:auth_user_changelist')

    def test_action_get(self):
        response = self.client.get(self._url, {'action': 'mass_update',
                                               'index': 0,
                                               'select_across': 0,
                                               '_selected_action': [2, 3, 4]})
        self.assertEqual(response.status_code, 302)
        self.assertIn('auth/user/?e=1', response['Location'])

    def test_action_post(self):
        target_ids = [2, 3, 4, 7, 10]
        response = self.client.post(self._url, {'select_across': 0,
                                                'action': 'mass_update',
                                                'index': 0,
                                                '_selected_action': target_ids})

        data = response.context['form'].initial
        data.update({'apply': 'Update records', 'chk_id_is_active': 1, 'func_id_is_active': 'set'})
        response = self.client.post(self._url, data)
        self.assertEquals(response.status_code, 302)
        self.assertSequenceEqual(target_ids, User.objects.filter(is_active=False).order_by('id').values_list('id', flat=True))

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
