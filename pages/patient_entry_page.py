"""Page object for the patient portal entry."""

from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from pages.base_page import BasePage


class PatientEntryPage(BasePage):
    """Open the patient portal and wait for its resulting route."""

    PATIENT_CENTER_HEADING = (By.XPATH, "//h1[normalize-space()='患者中心']")
    APPOINTMENTS_NAV = (By.CSS_SELECTOR, 'a[href="/patient/appointments"]')

    def __init__(
        self,
        driver,
        base_url: str = "http://localhost:8088",
        timeout: int = 10,
    ) -> None:
        super().__init__(driver, timeout)
        self.base_url = base_url.rstrip("/")

    def open_patient_portal(self) -> None:
        """Open the patient portal entry."""
        self.open(f"{self.base_url}/patient")

    def wait_for_login_redirect(self) -> str:
        """Wait until the browser reaches the login route."""
        self.wait.until(
            lambda driver: urlparse(driver.current_url).path.rstrip("/") == "/login"
        )
        return self.current_url

    def wait_for_document_ready(self) -> str:
        """Wait until the browser document has finished loading."""
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )
        return self.current_url

    def wait_for_patient_center_heading(self) -> WebElement:
        """Wait for the patient center heading after successful login."""
        return self.wait_visible(self.PATIENT_CENTER_HEADING)

    def wait_for_appointments_navigation(self) -> WebElement:
        """Wait for a patient-only navigation link to become visible."""
        return self.wait_visible(self.APPOINTMENTS_NAV)
