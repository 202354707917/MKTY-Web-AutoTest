"""Page object for the patient's profile page."""

from urllib.parse import urlparse

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class PatientProfilePage(BasePage):
    """Expose read-only patient profile information."""

    ROUTE = "/patient/profile"
    HEADING = (By.XPATH, "//main//h2[normalize-space()='个人中心']")
    USERNAME_VALUE = (
        By.XPATH,
        "//main//div[normalize-space()='用户名']/following-sibling::div[1]",
    )
    ROLE_VALUE = (
        By.XPATH,
        "//main//div[normalize-space()='角色']/following-sibling::div[1]",
    )
    NAME_VALUE = (
        By.XPATH,
        "//main//div[normalize-space()='姓名']/following-sibling::div[1]",
    )
    PHONE_VALUE = (
        By.XPATH,
        "//main//div[normalize-space()='手机号']/following-sibling::div[1]",
    )
    LOAD_ERROR = (By.CSS_SELECTOR, "[role='alert']")

    def open_profile(self, base_url: str = "http://localhost:8088") -> None:
        """Open the patient profile route directly."""
        self.open(f"{base_url.rstrip('/')}{self.ROUTE}")

    def wait_for_route(self) -> str:
        """Wait until the browser reaches the patient profile route."""
        self.wait.until(
            lambda driver: urlparse(driver.current_url).path.rstrip("/")
            == self.ROUTE
        )
        return self.current_url

    def wait_page_loaded(self) -> str:
        """Wait for document readiness and the profile heading."""
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )
        self.wait_visible(self.HEADING)
        self.wait_visible(self.USERNAME_VALUE)
        self.wait_visible(self.ROLE_VALUE)
        return self.current_url

    def _read_value(self, locator: tuple) -> str:
        """Read one profile value from the current DOM."""
        return self.wait_visible(locator).text.strip()

    def get_username(self) -> str:
        """Return the displayed username."""
        return self._read_value(self.USERNAME_VALUE)

    def get_role(self) -> str:
        """Return the displayed role label."""
        return self._read_value(self.ROLE_VALUE)

    def get_profile_info(self) -> dict[str, str]:
        """Return displayed profile fields without retaining page elements."""
        return {
            "name": self._read_value(self.NAME_VALUE),
            "username": self._read_value(self.USERNAME_VALUE),
            "phone": self._read_value(self.PHONE_VALUE),
            "role": self._read_value(self.ROLE_VALUE),
        }

    def is_profile_visible(self) -> bool:
        """Return whether the profile title and identity fields are visible."""
        try:
            self.wait_visible(self.HEADING)
            self.wait_visible(self.USERNAME_VALUE)
            self.wait_visible(self.ROLE_VALUE)
            return True
        except Exception:
            return False
