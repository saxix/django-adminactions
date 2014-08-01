# -*- coding: utf-8 -*-
from __future__ import absolute_import
import pytest  # noqa
import django  # noqa
import datetime
from time import sleep
from django.utils import dateformat
from .base import *  # noqa
from selenium.webdriver.support.select import Select


pytestmark = pytest.mark.selenium


@pytest.mark.skipif('django.VERSION[:2]==(1,8)')
def test_export_as_csv(admin_site):
    browser, administrator = admin_site
    browser.find_element_by_link_text("Demo models").click()
    browser.find_element_by_id("action-toggle").click()
    Select(browser.find_element_by_name("action")).select_by_visible_text("Export as CSV")
    browser.find_element_by_name("index").click()
    browser.find_element_by_name("apply").click()


@pytest.fixture
def export_csv_page(admin_site):
    browser, administrator = admin_site
    browser.go('/admin/')
    browser.find_element_by_link_text("Demo models").click()
    browser.find_element_by_id("action-toggle").click()
    Select(browser.find_element_by_name("action")).select_by_visible_text("Export as CSV")
    browser.find_element_by_name("index").click()
    return browser, administrator


def _test(browser, target, format, sample_num):
    fmt = browser.find_element_by_id(target)
    fmt.clear()
    fmt.send_keys(format)
    sleep(1)
    sample = browser.find_elements_by_css_selector("span.sample")[sample_num]
    expected_value = dateformat.format(datetime.datetime.now(), format)
    assert sample.text == expected_value, "Failed Ajax call on %s" % target


@pytest.mark.skipif('django.VERSION[:2]==(1,8)')
def test_datetime_format_ajax(export_csv_page):
    browser, administrator = export_csv_page
    _test(browser, "id_datetime_format", 'l, d F Y', 0)
    _test(browser, "id_date_format", 'd F Y', 1)
    _test(browser, "id_time_format", 'H:i', 2)

