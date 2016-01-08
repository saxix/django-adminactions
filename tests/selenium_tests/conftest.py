# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import types

import pytest
from django_dynamic_fixture import G
from selenium import webdriver

# from demo.common import *  # noqa

browsers = {
    'firefox': webdriver.Firefox,
    # 'chrome': webdriver.Chrome,
}


@pytest.fixture(scope='session',
                params=list(browsers.keys()))
def driver(request):
    if 'DISPLAY' not in os.environ:
        pytest.skip('Test requires display server (export DISPLAY)')

    b = browsers[request.param]()

    request.addfinalizer(lambda *args: b.quit())

    return b


@pytest.fixture(scope='session')
def browser(live_server, driver):
    '''Open a Selenium browser with window size and wait time set.'''

    def go(self, url):
        self._last_url = url
        return self.get(self.live_server.url + url)

    def dump(self, filename=None):
        dest = filename or self._last_url.replace('/', '_').replace('#', '~')
        self.get_screenshot_as_file('./{}.jpg'.format(dest))

    b = driver
    b.live_server = live_server
    b.set_window_size(1024, 768)
    b.implicitly_wait(10)

    b.go = types.MethodType(go, b)
    b.dump = types.MethodType(dump, b)

    return b


def login(browser):
    from utils import ADMIN, PWD

    browser.go('/admin/')

    username = browser.find_element_by_id('id_username')
    password = browser.find_element_by_id('id_password')

    username.send_keys(ADMIN)
    password.send_keys(PWD)

    browser.find_element_by_css_selector("input[type=\"submit\"]").click()

    return browser


@pytest.fixture(scope='function')
def admin_site(browser, administrator):
    from demo.models import DemoModel, UserDetail

    G(DemoModel, n=5)
    G(UserDetail, n=5)
    login(browser)
    return browser, administrator
