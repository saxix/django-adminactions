from __future__ import annotations

import os
import types

import pytest
from django_dynamic_fixture import G
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

browsers = {
    "firefox": webdriver.Firefox,
    'chrome': webdriver.Chrome,
}


@pytest.fixture(scope="session", params=list(browsers.keys()))
def driver(request) -> "WebDriver":
    if "DISPLAY" not in os.environ:
        pytest.skip("Test requires display server (export DISPLAY)")
    if request.param == "firefox":
        options = webdriver.FirefoxOptions()
        options.add_argument("-headless")
    else:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")  # for Chrome >= 109

    b = browsers[request.param](options=options)

    request.addfinalizer(lambda *args: b.quit())

    return b


@pytest.fixture(scope="session")
def browser(live_server, driver):
    """Open a Selenium browser with window size and wait time set."""

    def go(self, url):
        self._last_url = url
        return self.get(self.live_server.url + url)

    def dump(self, filename=None) -> None:
        dest = filename or self._last_url.replace("/", "_").replace("#", "~")
        self.get_screenshot_as_file(f"./{dest}.jpg")

    b = driver
    b.live_server = live_server
    b.set_window_size(1024, 768)
    b.implicitly_wait(10)

    b.go = types.MethodType(go, b)
    b.dump = types.MethodType(dump, b)

    return b


def login(browser):
    from utils import ADMIN, PWD

    browser.go("/")

    username = browser.find_element(By.ID, "id_username")
    password = browser.find_element(By.ID, "id_password")

    username.send_keys(ADMIN)
    password.send_keys(PWD)
    browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()

    return browser


@pytest.fixture
def admin_site(browser, administrator):
    from demo.models import DemoModel, UserDetail

    G(DemoModel, n=5)
    G(UserDetail, n=5)
    login(browser)
    return browser, administrator
