# -*- coding: utf-8 -*-
from __future__ import absolute_import

from selenium import webdriver

browsers = {
    # 'firefox': webdriver.Firefox,
    'chrome': webdriver.Chrome,
}


def login(browser):
    from utils import ADMIN, PWD
    browser.go('/admin/')
    username = browser.find_element_by_id('id_username')
    password = browser.find_element_by_id('id_password')

    username.send_keys(ADMIN)
    password.send_keys(PWD)

    browser.find_element_by_css_selector("input[type=\"submit\"]").click()

    return browser
