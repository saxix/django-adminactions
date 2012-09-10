from django.conf import global_settings
from django.test.testcases import TestCase

SETTINGS = {'MIDDLEWARE_CLASSES': global_settings.MIDDLEWARE_CLASSES,
            'INSTALLED_APPS': (
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.sites',
                'django.contrib.messages',
                'django.contrib.staticfiles',
                'django.contrib.admin',
                'adminactions',
                ),
            'AUTHENTICATION_BACKENDS': ('django.contrib.auth.backends.ModelBackend',),
            'TEMPLATE_LOADERS': ('django.template.loaders.filesystem.Loader',
                                 'django.template.loaders.app_directories.Loader'),
            'TEMPLATE_CONTEXT_PROCESSORS': ("django.contrib.auth.context_processors.auth",
                                            "django.core.context_processors.debug",
                                            "django.core.context_processors.i18n",
                                            "django.core.context_processors.media",
                                            "django.core.context_processors.static",
                                            "django.core.context_processors.request",
                                            "django.core.context_processors.tz",
                                            "django.contrib.messages.context_processors.messages"
                )
}

class BaseTestCase(TestCase):
    urls = 'adminactions.tests.urls'
    fixtures = ['adminactions.json', ]

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.sett = self.settings(**SETTINGS)
        assert self.client.login(username='sax', password='123')
        self.sett.enable()

    def tearDown(self):
        self.sett.disable()
