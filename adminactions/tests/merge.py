# -*- coding: utf-8 -*-
from django.utils.unittest import skipIf
from django.conf import settings
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User, Group, Permission
from django.core.urlresolvers import reverse
from django.test import TransactionTestCase
from adminactions.api import merge, ALL_FIELDS

from .common import BaseTestCaseMixin


def assert_profile(user):
    p = None
    try:
        user.get_profile()
    except ObjectDoesNotExist:
        app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
        model = models.get_model(app_label, model_name)
        p, __ = model.objects.get_or_create(user=user)

    return p


def get_profile(user):
    app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
    model = models.get_model(app_label, model_name)
    return model.objects.get(user=user)


class MergeTestApi(BaseTestCaseMixin, TransactionTestCase):
    urls = "adminactions.tests.urls"

    def setUp(self):
        super(MergeTestApi, self).setUp()
        self.master_pk = 2
        self.other_pk = 3

    def tearDown(self):
        super(MergeTestApi, self).tearDown()

    def test_merge_success_no_commit(self):
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        result = merge(master, other)

        self.assertTrue(User.objects.filter(pk=master.pk).exists())
        self.assertTrue(User.objects.filter(pk=other.pk).exists())

        self.assertEqual(result.pk, master.pk)
        self.assertEqual(result.first_name, other.first_name)
        self.assertEqual(result.last_name, other.last_name)
        self.assertEqual(result.password, other.password)

    def test_merge_success_fields_no_commit(self):
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        result = merge(master, other, ['password', 'last_login'])

        master = User.objects.get(pk=master.pk)

        self.assertTrue(User.objects.filter(pk=master.pk).exists())
        self.assertTrue(User.objects.filter(pk=other.pk).exists())

        self.assertNotEqual(result.last_login, master.last_login)
        self.assertEqual(result.last_login, other.last_login)
        self.assertEqual(result.password, other.password)

        self.assertNotEqual(result.last_name, other.last_name)

    def test_merge_success_commit(self):
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        result = merge(master, other, commit=True)

        master = User.objects.get(pk=result.pk)  # reload
        self.assertTrue(User.objects.filter(pk=master.pk).exists())
        self.assertFalse(User.objects.filter(pk=other.pk).exists())

        self.assertEqual(result.pk, master.pk)
        self.assertEqual(master.first_name, other.first_name)
        self.assertEqual(master.last_name, other.last_name)
        self.assertEqual(master.password, other.password)

    def test_merge_success_m2m(self):
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        group = Group.objects.get_or_create(name='G1')[0]
        other.groups.add(group)
        other.save()

        result = merge(master, other, commit=True, m2m=['groups'])
        master = User.objects.get(pk=result.pk)  # reload
        self.assertSequenceEqual(master.groups.all(), [group])

    def test_merge_success_m2m_all(self):
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        group = Group.objects.get_or_create(name='G1')[0]
        perm = Permission.objects.all()[0]
        other.groups.add(group)
        other.user_permissions.add(perm)
        other.save()

        merge(master, other, commit=True, m2m=ALL_FIELDS)
        self.assertSequenceEqual(master.groups.all(), [group])
        self.assertSequenceEqual(master.user_permissions.all(), [perm])

    def test_merge_success_related_all(self):
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        entry = other.logentry_set.get_or_create(object_repr='test', action_flag=1)[0]

        result = merge(master, other, commit=True, related=ALL_FIELDS)

        master = User.objects.get(pk=result.pk)  # reload
        self.assertSequenceEqual(master.logentry_set.all(), [entry])
        self.assertTrue(LogEntry.objects.filter(pk=entry.pk).exists())

    @skipIf(not hasattr(settings, 'AUTH_PROFILE_MODULE'), "")
    def test_merge_one_to_one_field(self):
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        profile = assert_profile(other)
        if profile:
            entry = other.logentry_set.get_or_create(object_repr='test', action_flag=1)[0]

            result = merge(master, other, commit=True, related=ALL_FIELDS)

            master = User.objects.get(pk=result.pk)  # reload
            self.assertSequenceEqual(master.logentry_set.all(), [entry])
            self.assertTrue(LogEntry.objects.filter(pk=entry.pk).exists())
            self.assertEqual(get_profile(result), profile)
            self.assertEqual(master.get_profile(), profile)


    def test_merge_ignore_related(self):
        master = User.objects.get(pk=self.master_pk)
        other = User.objects.get(pk=self.other_pk)
        entry = other.logentry_set.get_or_create(object_repr='test', action_flag=1)[0]
        result = merge(master, other, commit=True, related=None)

        master = User.objects.get(pk=result.pk)  # reload
        self.assertSequenceEqual(master.logentry_set.all(), [])
        self.assertFalse(User.objects.filter(pk=other.pk).exists())
        self.assertFalse(LogEntry.objects.filter(pk=entry.pk).exists())


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
