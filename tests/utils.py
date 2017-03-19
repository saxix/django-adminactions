# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import string
from random import choice, randrange, shuffle
from six.moves import range

from django.conf import global_settings
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
from django.contrib.auth import authenticate
from django.contrib.auth.models import Group, Permission, User
from django.forms import BaseForm
from django.test.testcases import TestCase
from django_dynamic_fixture import G
from django_dynamic_fixture.fixture_algorithms.random_fixture import \
    RandomDataFixture

from adminactions.exceptions import ActionInterrupted
from adminactions.signals import (adminaction_end, adminaction_requested,
                                  adminaction_start,)


class admin_register(object):
    def __init__(self, model, model_admin=None, unregister=False):
        self.model = model
        self.model_admin = model_admin
        self.unregister = unregister

    def __enter__(self):
        try:
            admin.site.register(self.model, self.model_admin)
            self.unregister = True
        except AlreadyRegistered:
            pass
        return admin.site._registry[self.model]

    def __exit__(self, *exc_info):
        if self.unregister:
            admin.site.unregister(self.model)

    def start(self):
        """Activate a patch, returning any created mock."""
        result = self.__enter__()
        return result

    def stop(self):
        """Stop an active patch."""
        return self.__exit__()


def text(length, choices=string.ascii_letters):
    """ returns a random (fixed length) string

    :param length: string length
    :param choices: string containing all the chars can be used to build the string

    .. seealso::
       :py:func:`rtext`
    """
    return ''.join(choice(choices) for x in range(length))


def get_group(name=None, permissions=None):
    group = G(Group, name=(name or text(5)))
    permission_names = permissions or []
    for permission_name in permission_names:
        try:
            app_label, codename = permission_name.split('.')
        except ValueError:
            raise ValueError("Invalid permission name `{0}`".format(permission_name))
        try:
            permission = Permission.objects.get(content_type__app_label=app_label, codename=codename)
        except Permission.DoesNotExist:
            raise Permission.DoesNotExist('Permission `{0}` does not exist'.format(permission_name))

        group.permissions.add(permission)
    return group


class user_grant_permission(object):
    def __init__(self, user, permissions=None):
        self.user = user
        self.permissions = permissions
        self.group = None

    def __enter__(self):
        if hasattr(self.user, '_group_perm_cache'):
            del self.user._group_perm_cache
        if hasattr(self.user, '_perm_cache'):
            del self.user._perm_cache
        self.group = get_group(permissions=self.permissions or [])
        self.user.groups.add(self.group)

    def __exit__(self, *exc_info):
        if self.group:
            self.user.groups.remove(self.group)
            self.group.delete()

    def start(self):
        """Activate a patch, returning any created mock."""
        result = self.__enter__()
        return result

    def stop(self):
        """Stop an active patch."""
        return self.__exit__()


class SelectRowsMixin(object):
    _selected_rows = []
    _selected_values = []
    csrf_checks = False

    def _select_rows(self, form, selected_rows=None):
        if selected_rows is None:
            selected_rows = self._selected_rows

        self._selected_values = []
        for r in selected_rows:
            chk = form.get('_selected_action', r, default=None)
            if chk:
                form.set('_selected_action', True, r)
                self._selected_values.append(int(chk.value))


class CheckSignalsMixin(object):
    MESSAGE = 'Action Interrupted Test'

    def test_signal_sent(self):
        def handler_factory(name):
            def myhandler(sender, action, request, queryset, **kwargs):
                handler_factory.invoked[name] = True
                self.assertEqual(action, self.action_name)
                self.assertSequenceEqual(queryset.order_by('id').values_list('id', flat=True),
                                         sorted(self._selected_values))

            return myhandler

        handler_factory.invoked = {}

        try:
            m1 = handler_factory('adminaction_requested')
            adminaction_requested.connect(m1, sender=self.sender_model)

            m2 = handler_factory('adminaction_start')
            adminaction_start.connect(m2, sender=self.sender_model)

            m3 = handler_factory('adminaction_end')
            adminaction_end.connect(m3, sender=self.sender_model)

            self._run_action()
            self.assertIn('adminaction_requested', handler_factory.invoked)
            self.assertIn('adminaction_start', handler_factory.invoked)
            self.assertIn('adminaction_end', handler_factory.invoked)

        finally:
            adminaction_requested.disconnect(m1, sender=self.sender_model)
            adminaction_start.disconnect(m2, sender=self.sender_model)
            adminaction_end.disconnect(m3, sender=self.sender_model)

    def test_signal_requested(self):
        # test if adminaction_requested Signal can stop the action

        def myhandler(sender, action, request, queryset, **kwargs):
            myhandler.invoked = True
            self.assertEqual(action, self.action_name)
            self.assertSequenceEqual(queryset.order_by('id').values_list('id', flat=True),
                                     sorted(self._selected_values))
            raise ActionInterrupted(self.MESSAGE)

        try:
            adminaction_requested.connect(myhandler, sender=self.sender_model)
            self._run_action(1)
            self.assertTrue(myhandler.invoked)
            self.assertIn(self.MESSAGE, self.app.cookies['messages'])
        finally:
            adminaction_requested.disconnect(myhandler, sender=self.sender_model)

    def test_signal_start(self):
        # test if adminaction_start Signal can stop the action

        def myhandler(sender, action, request, queryset, form, **kwargs):
            myhandler.invoked = True
            self.assertEqual(action, self.action_name)
            self.assertSequenceEqual(queryset.order_by('id').values_list('id', flat=True),
                                     sorted(self._selected_values))
            self.assertTrue(isinstance(form, BaseForm))
            raise ActionInterrupted(self.MESSAGE)

        try:
            adminaction_start.connect(myhandler, sender=self.sender_model)
            self._run_action(2)
            self.assertTrue(myhandler.invoked)
            self.assertIn(self.MESSAGE, self.app.cookies['messages'])
        finally:
            adminaction_start.disconnect(myhandler, sender=self.sender_model)

    def test_signal_end(self):
        # test if adminaction_start Signal can stop the action

        def myhandler(sender, action, request, queryset, **kwargs):
            myhandler.invoked = True
            self.assertEqual(action, self.action_name)
            self.assertSequenceEqual(queryset.order_by('id').values_list('id', flat=True),
                                     sorted(self._selected_values))

        try:
            adminaction_end.connect(myhandler, sender=self.sender_model)
            self._run_action(2)
            self.assertTrue(myhandler.invoked)
        finally:
            adminaction_end.disconnect(myhandler, sender=self.sender_model)


def ipaddress(not_valid=None):
    """
        returns a string representing a random ip address

    :param not_valid: if passed must be a list of integers representing valid class A netoworks that must be ignored
    """
    not_valid_class_A = not_valid or []

    class_a = [r for r in range(1, 256) if r not in not_valid_class_A]
    shuffle(class_a)
    first = class_a.pop()

    return ".".join([str(first), str(randrange(1, 256)),
                     str(randrange(1, 256)), str(randrange(1, 256))])


class DataFixtureClass(RandomDataFixture):  # it can inherit of SequentialDataFixture, RandomDataFixture etc.
    def genericipaddressfield_config(self, field, key):  # method name must have the format: FIELDNAME_config
        return ipaddress()


TEST_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__),
                                  os.pardir, 'tests', 'templates')
SETTINGS = {'MIDDLEWARE_CLASSES': global_settings.MIDDLEWARE_CLASSES,
            'TEMPLATE_DIRS': [TEST_TEMPLATES_DIR],
            'AUTHENTICATION_BACKENDS': ('django.contrib.auth.backends.ModelBackend',),
            'TEMPLATE_LOADERS': ('django.template.loaders.filesystem.Loader',
                                 'django.template.loaders.app_directories.Loader'),
            # 'AUTH_PROFILE_MODULE': None,
            'TEMPLATE_CONTEXT_PROCESSORS': ("django.contrib.auth.context_processors.auth",
                                            "django.core.context_processors.debug",
                                            "django.core.context_processors.i18n",
                                            "django.core.context_processors.media",
                                            "django.core.context_processors.static",
                                            "django.core.context_processors.request",
                                            "django.core.context_processors.tz",
                                            "django.contrib.messages.context_processors.messages")}

ADMIN = 'sax'
USER = 'user'
PWD = '123'
USER_EMAIL = 'user@moreply.org'


class BaseTestCaseMixin(object):
    fixtures = ['adminactions.json', ]

    def setUp(self):
        super(BaseTestCaseMixin, self).setUp()
        self.sett = self.settings(**SETTINGS)
        self.sett.enable()
        self.login()

    def tearDown(self):
        self.sett.disable()

    def login(self, username='user_00', password='123'):
        user = User.objects.get(username=username)
        try:
            self.client.force_login(user)
        except AttributeError:  # for Django<1.8
            logged = self.client.login(username=username, password=password)
            assert logged, 'Unable login with credentials'
        self._user = authenticate(username=username, password=password)

    def add_permission(self, *perms, **kwargs):
        """ add the right permission to the user """
        target = kwargs.pop('user', self._user)
        if hasattr(target, '_perm_cache'):
            del target._perm_cache
        for perm_name in perms:
            app_label, code = perm_name.split('.')
            if code == '*':
                perms = Permission.objects.filter(content_type__app_label=app_label)
            else:
                perms = Permission.objects.filter(codename=code, content_type__app_label=app_label)
            target.user_permissions.add(*perms)

        target.save()


class BaseTestCase(BaseTestCaseMixin, TestCase):
    pass
