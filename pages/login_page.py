"""Page object for the HuiYiTong login page."""

from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pages.base_page import BasePage


class LoginPage(BasePage):
    """Expose verified login-page locators and read-only operations."""

    HEADING = (By.XPATH, "//h1[normalize-space()='登录慧医通']")
    USERNAME_INPUT = (By.CSS_SELECTOR, 'input[autocomplete="username"]')
    PASSWORD_INPUT = (
        By.CSS_SELECTOR,
        'input[autocomplete="current-password"]',
    )
    SUBMIT_BUTTON = (By.CSS_SELECTOR, 'button[type="submit"]')
    ALERT = (By.CSS_SELECTOR, '[role="alert"]')

    def wait_for_heading(self) -> WebElement:
        """Wait for the expected login heading."""
        return self.wait_visible(self.HEADING)

    def wait_for_username_input(self) -> WebElement:
        """Wait for the username input to become visible."""
        return self.wait_visible(self.USERNAME_INPUT)

    def wait_for_password_input(self) -> WebElement:
        """Wait for the password input to become visible."""
        return self.wait_visible(self.PASSWORD_INPUT)

    def enter_username(self, username: str) -> None:
        """Enter a username without logging or exposing its value."""
        self.type_text(self.USERNAME_INPUT, username)

    def enter_password(self, password: str) -> None:
        """Enter a password without logging or exposing its value."""
        self.type_text(self.PASSWORD_INPUT, password)

    def submit(self) -> None:
        """Click the login form submit button."""
        self.click(self.SUBMIT_BUTTON)

    def wait_for_patient_route(self) -> str:
        """Wait until successful patient login reaches the patient route."""
        self.wait.until(
            lambda driver: urlparse(driver.current_url).path.rstrip("/") == "/patient"
        )
        return self.current_url

    def wait_for_alert(self, timeout: int | None = None) -> WebElement:
        """Wait for a visible login error alert and return it."""
        wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        return wait.until(EC.visibility_of_element_located(self.ALERT))

    def is_login_form_visible(self) -> bool:
        """Check whether the heading and both input fields are visible."""
        try:
            self.wait_for_heading()
            self.wait_for_username_input()
            self.wait_for_password_input()
            return True
        except Exception:
            return False

    def get_alert_if_present(self) -> WebElement | None:
        """Return a visible login alert if one exists; do not submit the form."""
        elements = self.driver.find_elements(*self.ALERT)
        for element in elements:
            if element.is_displayed():
                return element
        return None
