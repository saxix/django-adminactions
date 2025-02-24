from __future__ import annotations

import datetime
from time import sleep
from typing import TYPE_CHECKING

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from selenium.webdriver.remote.webdriver import WebDriver

FAKE_TIME = datetime.datetime(2020, 12, 25, 17, 5, 55)

pytestmark = pytest.mark.selenium


@pytest.fixture
def now(monkeypatch) -> None:
    class FixedDateTime:
        @classmethod
        def now(cls, tz=None) -> datetime.datetime:
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
def export_csv_page(admin_site: tuple["WebDriver", "User"]) -> tuple["WebDriver", "User"]:
    browser, administrator = admin_site
    browser.go("/")
    browser.find_element(By.LINK_TEXT, "Demo models").click()
    browser.find_element(By.ID, "action-toggle").click()
    Select(browser.find_element(By.NAME, "action")).select_by_visible_text("Export as CSV")
    browser.find_element(By.NAME, "index").click()
    return browser, administrator


@pytest.mark.parametrize(
    ["fmt", "expected"],
    [("l, d F Y", "Friday, 25 December 2020"), ("d F Y", "25 December 2020"), ("H:i", "17:05")],
    ids=["l, d F Y", "d F Y", "H:i"],
)
@pytest.mark.parametrize("target", ["id_datetime_format", "id_date_format", "id_time_format"], ids=["dt", "d", "t"])
def test_datetime_format_ajax(export_csv_page, now, target, fmt: str, expected) -> None:
    browser, _administrator = export_csv_page
    wait = WebDriverWait(browser, 10)
    el = browser.find_element(By.ID, target)
    el.clear()
    el.send_keys(fmt)
    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, f"span.sample.{target}"), expected))
    sample = browser.find_element(By.CSS_SELECTOR, f"span.sample.{target}")
    assert sample.text == expected, f"Failed Ajax call on {target}: Expected {expected}, got {sample.text}"
