from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from adminactions.tests.common import BaseTestCase, ExecuteActionMixin, CheckSignalsMixin


__all__ = ['MassUpdateTest', ]


class MassUpdateTest(ExecuteActionMixin, CheckSignalsMixin, BaseTestCase):
    urls = "adminactions.tests.urls"
    selected_rows = [2, 3, 4, 7, 10]
    action_name = 'mass_update'
    sender_model = User

    def setUp(self):
        super(MassUpdateTest, self).setUp()
        self._url = reverse('admin:auth_user_changelist')
        self.add_permission('auth.adminactions_massupdate_user')

    def _run_action(self, code1=200, code2=200, code3=200, **kwargs):
        kwargs['apply_data'] = {'apply': 'Update records', 'chk_id_is_active': 1, 'func_id_is_active': 'set'}
        return super(MassUpdateTest, self)._run_action(code1, code2, 302, **kwargs)

    def test_action_post(self):
        response = self._run_action()
        self.assertEquals(response.status_code, 302)
        self.assertSequenceEqual(self.selected_rows,
                                 User.objects.filter(is_active=False).order_by('id').values_list('id', flat=True))

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
