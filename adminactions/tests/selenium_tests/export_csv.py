from time import sleep
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from selenium.webdriver.support.select import Select
from adminactions.tests.selenium_tests.common import FireFoxLiveTest, ChromeDriverMixin


__all__ = ['ExportCSVFireFox', ]


class ExportCSVFireFox(FireFoxLiveTest):
    def setUp(self):
        super(ExportCSVFireFox, self).setUp()
        self.factory = RequestFactory()
        self._url = reverse('admin:auth_user_changelist')

    def _go_to_page(self):
        self.login()
        driver = self.driver
        self.go(self._url)
        self.assertTrue("Select user to change" in driver.title)
        driver.find_element_by_xpath("//input[@id='action-toggle']").click() # select all
        driver.find_element_by_xpath("//input[@name='_selected_action' and @value='1']").click() # unselect sax
        Select(driver.find_element_by_name("action")).select_by_visible_text("Export as csv")
        driver.find_element_by_name("index").click() # execute
        self.assertTrue("Export to CSV" in driver.title)

    def _test(self, target, format, sample_num):
        self._go_to_page()
        driver = self.driver
        fmt = driver.find_element_by_id(target)
        sample = driver.find_elements_by_css_selector("span.sample")[sample_num]
        request = self.factory.get('', {'fmt': format})
        expected_value = reg.site1.format_date(request).content
        fmt.clear()
        fmt.send_keys(format)
        sleep(1)
        self.assertEquals(sample.text, expected_value)

    def test_datetime_format_ajax(self):
        self._test("id_datetime_format", 'l, d F Y', 0)

    def test_date_format_ajax(self):
        self._test("id_date_format", 'd F Y', 1)

    def test_time_format_ajax(self):
        self._test("id_time_format", 'H:i', 2)


class ExportCSVChrome(ChromeDriverMixin, ExportCSVFireFox):
    pass
