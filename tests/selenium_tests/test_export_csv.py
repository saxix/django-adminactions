from __future__ import annotations

import datetime
from time import sleep
from typing import TYPE_CHECKING

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from selenium.webdriver.remote.webdriver import WebDriver

FAKE_TIME = datetime.datetime(2020, 12, 25, 17, 5, 55)

pytestmark = pytest.mark.selenium


@pytest.fixture
def now(monkeypatch) -> None:
    class FixedDateTime:
        @classmethod
        def now(cls):
            return FAKE_TIME

    monkeypatch.setattr("adminactions.views.datetime", FixedDateTime)


def test_export_as_csv(admin_site: tuple["WebDriver", "User"]) -> None:
    browser, _administrator = admin_site
    browser.find_element(By.LINK_TEXT, "Demo models").click()
    browser.find_element(By.ID, "action-toggle").click()
    Select(browser.find_element(By.NAME, "action")).select_by_visible_text("Export as CSV")
    browser.find_element(By.NAME, "index").click()
    browser.find_element(By.NAME, "apply").click()


@pytest.fixture
def export_csv_page(admin_site: tuple["WebDriver", "User"]):
    browser, administrator = admin_site
    browser.go("/")
    browser.find_element(By.LINK_TEXT, "Demo models").click()
    browser.find_element(By.ID, "action-toggle").click()
    Select(browser.find_element(By.NAME, "action")).select_by_visible_text("Export as CSV")
    browser.find_element(By.NAME, "index").click()
    return browser, administrator


def _test(browser, target, format, sample_num, expected_value) -> None:
    fmt = browser.find_element(By.ID, target)
    fmt.clear()
    fmt.send_keys(format)
    sleep(1)
    sample = browser.find_elements(By.CSS_SELECTOR, "span.sample")[sample_num]
    # expected_value = dateformat.format(datetime.datetime.now(), format)
    assert sample.text == expected_value, f"Failed Ajax call on {target}"


# @pytest.mark.skipif('django.VERSION[:2]==(1,8)')
def test_datetime_format_ajax(export_csv_page, now) -> None:
    browser, _administrator = export_csv_page
    _test(browser, "id_datetime_format", "l, d F Y", 0, "Friday, 25 December 2020")
    _test(browser, "id_date_format", "d F Y", 1, "25 December 2020")
    _test(browser, "id_time_format", "H:i", 2, "17:05")
