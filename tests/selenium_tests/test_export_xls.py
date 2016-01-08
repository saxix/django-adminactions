# -*- coding: utf-8 -*-
from __future__ import absolute_import

import pytest
from selenium.webdriver.support.select import Select

pytestmark = pytest.mark.selenium


def test_export_xls(admin_site):
    browser, administrator = admin_site
    browser.go('/admin/')
    browser.find_element_by_link_text("Demo models").click()
    browser.find_element_by_id("action-toggle").click()
    Select(browser.find_element_by_name("action")).select_by_visible_text("Export as XLS")
    browser.find_element_by_name("index").click()
    browser.find_element_by_name("apply").click()
    return browser, administrator
