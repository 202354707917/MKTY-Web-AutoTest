"""Page object for a patient's doctor detail page."""

from urllib.parse import urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from pages.base_page import BasePage


class PatientDoctorDetailPage(BasePage):
    """Expose read-only doctor detail page checks."""

    ROUTE_PREFIX = "/patient/doctors/"
    DOCTOR_NAME = (By.XPATH, "//main//h2[1]")
    DEPARTMENT = (By.XPATH, "//main//h2[1]/following-sibling::p[1]")
    SPECIALTY = (
        By.XPATH,
        "//main//span[normalize-space()='擅长：']/parent::p",
    )
    BOOK_BUTTON = (
        By.XPATH,
        "//main//button[@type='submit' and normalize-space()='确认预约']",
    )
    AVAILABLE_SCHEDULES = (
        By.XPATH,
        "//main//form//button[@type='button' and not(@disabled)]",
    )

    def open(self, url: str) -> None:
        """Open the supplied doctor detail URL."""
        super().open(url)

    def wait_page_loaded(self) -> str:
        """Wait for document readiness and the doctor detail heading."""
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )
        self.wait_visible(self.DOCTOR_NAME)
        return self.current_url

    def wait_for_route(self) -> str:
        """Wait until the browser reaches a doctor detail route."""
        try:
            self.wait.until(
                lambda driver: (
                    urlparse(driver.current_url).path.startswith(self.ROUTE_PREFIX)
                    and urlparse(driver.current_url).path.rstrip("/")
                    != self.ROUTE_PREFIX.rstrip("/")
                )
            )
        except TimeoutException as exc:
            raise TimeoutException(
                "Timed out waiting for the doctor detail route. "
                f"Current URL: {self.current_url}; "
                f"Expected path: {self.ROUTE_PREFIX}<id>"
            ) from exc
        return self.current_url

    def get_doctor_name(self) -> str:
        """Return the visible doctor name from the detail heading."""
        return self.wait_visible(self.DOCTOR_NAME).text.strip()

    def is_detail_page_visible(self) -> bool:
        """Return whether the doctor name, department, and specialty are visible."""
        try:
            self.wait_visible(self.DOCTOR_NAME)
            self.wait_visible(self.DEPARTMENT)
            self.wait_visible(self.SPECIALTY)
            return True
        except Exception:
            return False

    def is_booking_button_visible(self) -> bool:
        """Return whether the read-only view exposes the booking button."""
        return any(
            element.is_displayed()
            for element in self.driver.find_elements(*self.BOOK_BUTTON)
        )

    def find_available_schedule(self) -> list[WebElement]:
        """Return visible and enabled schedule buttons without selecting them."""
        def find_slots(driver):
            slots = [
                element
                for element in driver.find_elements(*self.AVAILABLE_SCHEDULES)
                if element.is_displayed() and element.is_enabled()
            ]
            return slots or False

        try:
            return self.wait.until(find_slots)
        except TimeoutException as exc:
            raise RuntimeError("No available schedule slot was found") from exc

    def select_first_available_schedule(self) -> WebElement:
        """Select the first available schedule without submitting the booking."""
        slot = self.find_available_schedule()[0]
        slot.click()
        return slot
