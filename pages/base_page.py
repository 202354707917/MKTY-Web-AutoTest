"""Reusable Selenium page operations with explicit waits."""

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    """Provide common browser interactions for page objects."""

    def __init__(self, driver: WebDriver, timeout: int = 10) -> None:
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def open(self, url: str) -> None:
        """Navigate to the specified URL."""
        self.driver.get(url)

    def wait_visible(self, locator: tuple) :
        """Wait until an element is visible and return it."""
        return self.wait.until(EC.visibility_of_element_located(locator))

    def wait_clickable(self, locator: tuple):
        """Wait until an element is clickable and return it."""
        return self.wait.until(EC.element_to_be_clickable(locator))

    def find_visible(self, locator: tuple):
        """Find an element after waiting for visibility."""
        return self.wait_visible(locator)

    def click(self, locator: tuple) -> None:
        """Click an element after waiting until it is clickable."""
        self.wait_clickable(locator).click()

    def type_text(self, locator: tuple, text: str, *, clear: bool = True) -> None:
        """Type text into a visible input."""
        element = self.wait_visible(locator)
        if clear:
            element.clear()
        element.send_keys(text)

    @property
    def current_url(self) -> str:
        """Return the current browser URL."""
        return self.driver.current_url

    @property
    def title(self) -> str:
        """Return the current page title."""
        return self.driver.title
