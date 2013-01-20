# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.test import TransactionTestCase

from django.utils.translation import gettext as _
from .common import BaseTestCase, BaseTestCaseMixin


class MergeTest(BaseTestCaseMixin, TransactionTestCase):
    urls = "adminactions.tests.urls"

    def setUp(self):
        self.url = reverse('admin:auth_user_changelist')
        super(MergeTest, self).setUp()

    def test_error_if_too_many_records(self):
        response = self.client.post(self.url, {'action': 'merge', 'select_across': 0, '_selected_action': [2, 3, 4]})
        self.assertEqual(response.status_code, 302)
        self.assertIn("Please select exactly 2 records", response.cookies['messages'].value)

    def _action_init(self):
        FIRST, SECOND = 2, 3
        url = reverse('admin:auth_user_changelist')
        base_data = {'action': 'merge', 'select_across': 0, '_selected_action': [FIRST, SECOND]}
        response = self.client.post(url, base_data)
        other = response.context['other']
        master = response.context['master']

        assert master.username != other.username
        assert master.email != other.email
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Merge records")
        data = response.context['adminform'].form.initial
        other_data = response.context['formset'][1].initial
        master_data = response.context['formset'][0].initial
        assert other.username == other_data['username'], (other.username, other_data['username'])
        assert master.username == master_data['username'], (master.username, master_data['username'])
        assert data.get('username') == master_data['username'] != other_data['username']
        assert data['email'] != other_data['email']

        return response, master, other, base_data, data, master_data, other_data

    def _action_preview(self, data):
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'adminactions/merge_preview.html')
        self.assertContains(response, "Preview")
        self.assertIn('original', response.context)
        return response

    def test_success(self):
        response, master, other, base_data, data, master_data, other_data = self._action_init()
        # merge
        data['first_name'] = other_data['first_name']
        data['email'] = other_data['email']
        data['preview'] = 'preview'

        # we need to override these values because form.initial values are not valid
        # as widget's entry for date/datetime
        data['last_login'] = response.context['formset'][0]['last_login'].value()
        data['date_joined'] = response.context['formset'][0]['date_joined'].value()
        response = self._action_preview(data)

        data = response.context['adminform'].form.data
        data.update(base_data)
        del data['preview']
        data['apply'] = 'apply'
        assert data['first_name'] == other_data['first_name'] != master_data['first_name']

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        merged_record = User.objects.get(pk=master.pk)
        self.assertFalse(User.objects.filter(pk=other.pk).exists())

        self.assertEqual(merged_record.first_name, other.first_name)
        self.assertEqual(merged_record.email, other.email)

    def test_swap(self):
        response, master, other, base_data, data, master_data, other_data = self._action_init()

        data['first_name'] = other_data['first_name']
        data['email'] = other_data['email']
        data['preview'] = 'preview'
        #swap records. We want preserve 'other'
        data['master_pk'] = other.pk
        data['other_pk'] = master.pk

        # we need to override these values because form.initial values are not valid
        # as widget's entry for date/datetime
        data['last_login'] = response.context['formset'][0]['last_login'].value()
        data['date_joined'] = response.context['formset'][0]['date_joined'].value()

        response = self._action_preview(data)
        data = response.context['adminform'].form.data
        data.update(base_data)
        del data['preview']
        data['apply'] = 'apply'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        merged_record = User.objects.get(pk=other.pk)
        self.assertFalse(User.objects.filter(pk=master.pk).exists())

        self.assertEqual(merged_record.first_name, other.first_name)
        self.assertEqual(merged_record.email, other.email)

    def test_signal_start(self):
        pass
