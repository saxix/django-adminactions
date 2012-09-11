import os
from django.utils.unittest.case import skip
from django.conf import settings
from django.test import LiveServerTestCase

import time
from adminactions.tests.common import SETTINGS


selenium_can_start = lambda: getattr(settings, 'ENABLE_SELENIUM', True) and 'DISPLAY' in os.environ

try:
    import selenium.webdriver.firefox.webdriver
    import selenium.webdriver.chrome.webdriver
    from selenium.webdriver.support.wait import WebDriverWait
except ImportError as e:
    selenium_can_start = lambda: False


class SkipSeleniumTestChecker(type):
    def __new__(mcs, name, bases, attrs):
        super_new = super(SkipSeleniumTestChecker, mcs).__new__
        if not selenium_can_start():
            for name, func in attrs.items():
                if callable(func) and name.startswith('test'):
                    attrs[name] = skip('Selenium disabled')(func)
        return type.__new__(mcs, name, bases, attrs)


class SeleniumTestCase(LiveServerTestCase):
    __metaclass__ = SkipSeleniumTestChecker

    urls = 'adminactions.tests.urls'
    fixtures = ['adminactions.json', ]
    driver = None

    def _pre_setup(self):
        super(SeleniumTestCase, self)._pre_setup()
        self.sett = self.settings(**SETTINGS)
        self.sett.enable()

    def _post_teardown(self):
        super(SeleniumTestCase, self)._post_teardown()
        time.sleep(1)
        self.sett.disable()

    @classmethod
    def setUpClass(cls):
        if selenium_can_start():
            super(SeleniumTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        if selenium_can_start():
            super(SeleniumTestCase, cls).tearDownClass()

    @property
    def base_url(self):
        return self.live_server_url

    def setUp(self):
        super(SeleniumTestCase, self).setUp()
        if selenium_can_start():
            self.driver = self.driverClass()

    def tearDown(self):
        super(SeleniumTestCase, self).tearDown()
        if self.driver:
            self.driver.quit()

    def go(self, url):
        self.driver.get('%s%s' % (self.live_server_url, url))

    def login(self, url='/admin/'):
        u = '%s%s' % (self.live_server_url, url)
        self.driver.get(u)
        time.sleep(3)
        username_input = self.driver.find_element_by_name("username")
        username_input.send_keys('sax')
        password_input = self.driver.find_element_by_name("password")
        password_input.send_keys('123')
        self.driver.find_element_by_xpath('//input[@type="submit"]').click()
        WebDriverWait(self.driver, 5).until(lambda driver: driver.find_element_by_id('site-name'))
        self.assertTrue("Welcome, sax" in self.driver.find_element_by_id('user-tools').text)


class FirefoxDriverMixin(object):
    driverClass = selenium.webdriver.firefox.webdriver.WebDriver


class ChromeDriverMixin(object):
    driverClass = selenium.webdriver.chrome.webdriver.WebDriver


class FireFoxLiveTest(FirefoxDriverMixin, SeleniumTestCase):
    pass
#    INSTALLED_APPS = (
#        'django.contrib.auth',
#        'django.contrib.contenttypes',
#        'django.contrib.sessions',
#        'django.contrib.sites',
#        'django.contrib.messages',
#        'django.contrib.staticfiles',
#        'iadmin',
#        'django.contrib.admin',
#        'django.contrib.admindocs',
#        'geo',
#        )

#    def setUp(self):
#        self.settings(SETTINGS)
#        super(FireFoxLiveTest, self).setUp()


