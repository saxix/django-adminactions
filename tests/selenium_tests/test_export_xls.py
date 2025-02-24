from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

pytestmark = pytest.mark.selenium
if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from selenium.webdriver.remote.webdriver import WebDriver


def test_export_xls(admin_site: tuple["WebDriver", "User"]):
    browser, administrator = admin_site
    browser.go("/")
    browser.find_element(By.LINK_TEXT, "Demo models").click()
    browser.find_element(By.ID, "action-toggle").click()
    Select(browser.find_element(By.NAME, "action")).select_by_visible_text("Export as XLS")
    browser.find_element(By.NAME, "index").click()
    browser.find_element(By.NAME, "apply").click()
    return browser, administrator
