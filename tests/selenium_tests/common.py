from __future__ import absolute_import
# import os
# from django.utils.unittest.case import skip
# from django.conf import settings
# from django.test import LiveServerTestCase
# import time
# from tests.common import SETTINGS
#
#
# try:
#     import selenium.webdriver.firefox.webdriver
#     import selenium.webdriver.chrome.webdriver
#     from selenium.webdriver.support.wait import WebDriverWait
#
#     def selenium_can_start():
#         return getattr(settings, 'ENABLE_SELENIUM',
#                        not os.environ.get('DISABLE_SELENIUM', 0)) and 'DISPLAY' in os.environ
#
#
# except ImportError as e:
#     selenium_can_start = lambda: False
#
#
# class SkipSeleniumTestChecker(type):
#     def __new__(mcs, name, bases, attrs):
#         if not selenium_can_start():
#             for name, func in attrs.items():
#                 if callable(func) and name.startswith('test'):
#                     attrs[name] = skip('Selenium disabled')(func)
#         return type.__new__(mcs, name, bases, attrs)
#
#
# class SeleniumTestCase(LiveServerTestCase):
#     __metaclass__ = SkipSeleniumTestChecker
#
#     urls = 'adminactions.tests.urls'
#     fixtures = ['adminactions.json', ]
#     driver = None
#
#     def _pre_setup(self):
#         super(SeleniumTestCase, self)._pre_setup()
#         self.sett = self.settings(**SETTINGS)
#         self.sett.enable()
#
#     def _post_teardown(self):
#         super(SeleniumTestCase, self)._post_teardown()
#         time.sleep(1)
#         self.sett.disable()
#
#     @classmethod
#     def setUpClass(cls):
#         if selenium_can_start():
#             super(SeleniumTestCase, cls).setUpClass()
#
#     @classmethod
#     def tearDownClass(cls):
#         if selenium_can_start():
#             super(SeleniumTestCase, cls).tearDownClass()
#
#     @property
#     def base_url(self):
#         return self.live_server_url
#
#     def setUp(self):
#         super(SeleniumTestCase, self).setUp()
#         if selenium_can_start():
#             self.driver = self.driverClass()
#
#     def tearDown(self):
#         super(SeleniumTestCase, self).tearDown()
#         if self.driver:
#             self.driver.quit()
#
#     def go(self, url):
#         self.driver.get('%s%s' % (self.live_server_url, url))
#
#     def login(self, url='/admin/'):
#         u = '%s%s' % (self.live_server_url, url)
#         self.driver.get(u)
#         time.sleep(3)
#         username_input = self.driver.find_element_by_name("username")
#         username_input.send_keys('sax')
#         password_input = self.driver.find_element_by_name("password")
#         password_input.send_keys('123')
#         self.driver.find_element_by_xpath('//input[@type="submit"]').click()
#         WebDriverWait(self.driver, 5).until(lambda driver: driver.find_element_by_id('site-name'))
#         self.assertTrue("Welcome, sax" in self.driver.find_element_by_id('user-tools').text)
#
#
# class FirefoxDriverMixin(object):
#     driverClass = selenium.webdriver.firefox.webdriver.WebDriver
#
#
# class ChromeDriverMixin(object):
#     driverClass = selenium.webdriver.chrome.webdriver.WebDriver
#
#
# class FireFoxLiveTest(FirefoxDriverMixin, SeleniumTestCase):
#     pass
#
# #    INSTALLED_APPS = (
# #        'django.contrib.auth',
# #        'django.contrib.contenttypes',
# #        'django.contrib.sessions',
# #        'django.contrib.sites',
# #        'django.contrib.messages',
# #        'django.contrib.staticfiles',
# #        'iadmin',
# #        'django.contrib.admin',
# #        'django.contrib.admindocs',
# #        'geo',
# #        )
#
# #    def setUp(self):
# #        self.settings(SETTINGS)
# #        super(FireFoxLiveTest, self).setUp()


import pytest
import os
from selenium import webdriver

browsers = {
    # 'firefox': webdriver.Firefox,
    'chrome': webdriver.Chrome,
}


@pytest.fixture(scope='session',
                params=list(browsers.keys()))
def driver(request):
    if 'DISPLAY' not in os.environ:
        pytest.skip('Test requires display server (export DISPLAY)')

    b = browsers[request.param]()

    request.addfinalizer(lambda *args: b.quit())

    return b


@pytest.fixture(scope='function')
def browser(driver):
    '''Open a Selenium browser with window size and wait time set.'''
    b = driver
    b.set_window_size(1400, 800)

    # Wait for elements/conditions to appear. This slows down the tests
    # somewhat in Firefox, but it makes them more reliable.
    b.implicitly_wait(5)

    return b


@pytest.fixture(scope='function')
def logged_admin(browser):
    browser.get('http://localhost:8000/')
    username = browser.find_element_by_id('id_username')
    password = browser.find_element_by_id('id_password')

    username.send_keys('sax')
    password.send_keys('123')

    browser.find_element_by_id('login').click()

    return browser
