# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import types

import pytest
from django_dynamic_fixture import G
from selenium import webdriver

from demo.common import *  # noqa
from demo.models import DemoModel, UserDetail

browsers = {
    # 'firefox': webdriver.Firefox,
    'chrome': webdriver.Chrome,
}

def login(browser):
    browser.go('/admin/')
    username = browser.find_element_by_id('id_username')
    password = browser.find_element_by_id('id_password')

    username.send_keys(ADMIN)
    password.send_keys(PWD)

    browser.find_element_by_css_selector("input[type=\"submit\"]").click()

    return browser
