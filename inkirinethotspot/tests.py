import os

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright


# Playwright runs and eventloop to control the browser, so Django async
# safety checks will fail, for more details check [django docs][1].
#
# [1]: https://docs.djangoproject.com/en/3.1/topics/async/#async-safety

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"


class AcceptanceTests(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=False)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def test_when_no_contract_then_error(self):
        page = self.browser.new_page()
        page.goto(self.live_server_url, timeout=5000)
        page.fill('#id_email', 'foobar@example.com')
        page.click('css=[type="submit"]')
        error = page.text_content('li')
        self.assertIn("Sorry, this contract was not found", error)
        page.close()
