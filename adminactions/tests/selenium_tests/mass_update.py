from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from .common import FireFoxLiveTest, ChromeDriverMixin
from selenium.webdriver.support.ui import Select
#from reg import site1 as site

__all__ = ['MassUpdateFireFox']


class MassUpdateFireFox(FireFoxLiveTest):
    def setUp(self):
        super(MassUpdateFireFox, self).setUp()
        self._url = reverse('admin:auth_user_changelist')

    def test_mass_update_1(self):
        """
        Check Boolean Field.
        Common values are not filled in boolean fields ( there is no reason to do that ).
        """
        self.login()
        driver = self.driver
        self.go(self._url)
        self.assertIn("Select user to change", driver.title)
        driver.find_element_by_xpath("//input[@id='action-toggle']").click() # select all
        driver.find_element_by_xpath("//input[@name='_selected_action' and @value='1']").click() # unselect sax
        Select(driver.find_element_by_name("action")).select_by_visible_text("Mass update")
        driver.find_element_by_name("index").click() # execute
        self.assertIn("Mass update users", driver.title)
        driver.find_element_by_xpath("//div[@id='col1']/form/table/tbody/tr[10]/td[5]/a[2]").click() # False
        driver.find_element_by_name("apply").click()
        self.assertIn("Select user to change", driver.title)


class MassUpdateChrome(ChromeDriverMixin, MassUpdateFireFox):
    pass
