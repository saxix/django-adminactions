import os
from adminactions.tests.selenium_tests.common import FireFoxLiveTest

__all__ = ['CSVImportTest', 'CSVImportFireFox']

DATADIR = os.path.join(os.path.dirname(__file__), 'data')


class CSVImportFireFox(FireFoxLiveTest):
    urls = 'iadmin.tests.urls'
    fixtures = ['test.json', ]
#
#    def test_impoty(self):
#        """
#        Check Boolean Field.
#        Common values are not filled in boolean fields ( there is no reaseon to do that ). Always show
#        """
#        csv_file = os.path.realpath(os.path.join(os.path.dirname(__file__), 'data', 'user_with_headers.csv'))
#        self.login()
#        driver = self.driver
#        driver.get(self.base_url + "/admin/")
#        driver.find_element_by_link_text("Users").click()
#        driver.find_element_by_link_text("import").click()
#        self.assertTrue("Import CSV File" in driver.title)
#        # ok stop here there is no way to laod a file via javascript :(
