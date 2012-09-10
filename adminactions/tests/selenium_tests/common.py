from django.conf import settings, global_settings
from django.test import LiveServerTestCase
import selenium.webdriver.firefox.webdriver
import selenium.webdriver.chrome.webdriver
import time
from adminactions.tests.common import SETTINGS


class SeleniumTestCase(LiveServerTestCase):
    urls = 'adminactions.tests.urls'
    fixtures = ['adminactions.json', ]

#    def _pre_setup(self):
#        LiveServerTestCase._pre_setup(self)
#        self.sett = self.settings(**SETTINGS)
#        self.sett.enable()
#
#    def _post_teardown(self):
#        LiveServerTestCase._post_teardown(self)
#        time.sleep(1)
#        self.sett.disable()

    @property
    def base_url(self):
        return self.live_server_url

    @classmethod
    def setUpClass(cls):
        cls.driver = cls.driverClass()
        super(SeleniumTestCase, cls).setUpClass()
        settings.LANGUAGE_CODE = 'en-US'

    @classmethod
    def tearDownClass(cls):
        super(SeleniumTestCase, cls).tearDownClass()
        cls.driver.quit()

    def setUp(self):
        super(SeleniumTestCase, self).setUp()
        self.sett = self.settings(**SETTINGS)
        self.sett.enable()

    def tearDown(self):
        super(SeleniumTestCase, self).tearDown()
        time.sleep(1)
        self.sett.disable()

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
        time.sleep(1)
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


