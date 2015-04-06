from __future__ import absolute_import
import os
import pytest
from django.conf import global_settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import Permission, User
from django.test.testcases import TestCase

TEST_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), os.pardir, 'tests', 'templates')
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


@pytest.fixture(scope='function')
def administrator():
    superuser = User._default_manager.create_superuser(username=ADMIN,
                                                       password=PWD,
                                                       email="sax@noreply.org")
    return superuser




