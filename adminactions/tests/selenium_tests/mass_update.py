from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from iadmin.tests.selenium_tests.common import FireFoxLiveTest, ChromeDriverMixin
from selenium.webdriver.support.ui import Select
#from reg import site1 as site

__all__ = ['MassUpdateFireFox']

class MassUpdateFireFox(FireFoxLiveTest):
    def setUp(self):
        super(MassUpdateFireFox, self).setUp()
        self.factory = RequestFactory()
        self._url = reverse('iadmin:auth_user_changelist')

    def test_mass_update_1(self):
        """
        Check Boolean Field.
        Common values are not filled in boolean fields ( there is no reaseon to do that ). Always show
        """

        self.login()
        driver = self.driver
        self.go(self._url)
        self.assertEqual("Select user to change | iAdmin console", driver.title)
        driver.find_element_by_xpath("//input[@id='action-toggle']").click() # select all
        driver.find_element_by_xpath("//input[@name='_selected_action' and @value='1']").click() # unselect sax
        Select(driver.find_element_by_name("action")).select_by_visible_text("Mass update")
        driver.find_element_by_name("index").click() # execute
        self.assertEqual("Mass update users | iAdmin console", driver.title)
        driver.find_element_by_xpath("//div[@id='col1']/form/table/tbody/tr[10]/td[4]/a[2]").click() # False
        driver.find_element_by_name("apply").click()
        self.assertEqual("Select user to change | iAdmin console", driver.title)
        queryset = User.objects.filter(is_active=True)
        self.assertAlmostEqual(len(queryset), 1)


class MassUpdateChrome(ChromeDriverMixin, MassUpdateFireFox):
    pass
