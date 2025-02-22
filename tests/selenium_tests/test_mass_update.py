from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from django.contrib.auth.models import User

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

pytestmark = pytest.mark.selenium


def test_mass_update_1(admin_site: tuple["WebDriver", "User"]) -> None:
    """
    Check Boolean Field.
    Common values are not filled in boolean fields ( there is no reason to do that ).
    """
    assert User.objects.filter(is_active=True).count() > 1  # sanity check
    sax = User.objects.get(username="sax")
    browser, _administrator = admin_site
    browser.find_element(By.LINK_TEXT, "Users").click()
    browser.find_element(By.ID, "action-toggle").click()
    browser.find_element(By.XPATH, f"//input[@name='_selected_action' and @value='{sax.pk}']").click()  # unselect sax

    Select(browser.find_element(By.NAME, "action")).select_by_visible_text("Mass update")
    browser.find_element(By.NAME, "index").click()  # execute

    assert "Mass update (users)" in browser.title
    browser.find_element(By.NAME, "chk_id_is_active").click()
    browser.find_element(By.ID, "id_is_active").click()
    browser.find_element(By.NAME, "apply").click()
    assert "Select user to change" in browser.title
    assert User.objects.filter(is_active=True).count() == 1
