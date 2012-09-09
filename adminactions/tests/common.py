from django.conf import global_settings
from django.test.testcases import TestCase


class BaseTestCase(TestCase):
    urls = 'adminactions.tests.urls'
    fixtures = ['adminactions.json', ]

    def setUp(self):
        super(BaseTestCase, self).setUp()
        assert self.client.login(username='sax', password='123')
        self.sett = self.settings(MIDDLEWARE_CLASSES=global_settings.MIDDLEWARE_CLASSES)
        self.sett.enable()

    def tearDown(self):
        self.sett.disable()
