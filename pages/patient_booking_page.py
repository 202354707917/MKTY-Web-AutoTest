"""Page object for the patient's booking interaction."""

import logging
from urllib.parse import urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class PatientBookingPage(BasePage):
    """Expose schedule selection and guarded booking operations."""

    APPOINTMENTS_ROUTE = "/patient/appointments"
    DOCTOR_NAME = (By.XPATH, "//main//h2[1]")
    SCHEDULE_HEADING = (By.XPATH, "//main//h3[normalize-space()='选择号源并预约']")
    AVAILABLE_SLOTS = (
        By.XPATH,
        "//main//form//button[@type='button' and not(@disabled)]",
    )
    SUBMIT_BUTTON = (
        By.XPATH,
        "//main//form//button[@type='submit' and normalize-space()='确认预约']",
    )
    NOTE_INPUT = (By.CSS_SELECTOR, "textarea")
    SUCCESS_HEADING = (By.XPATH, "//main//h2[normalize-space()='我的预约']")
    ERROR_ALERT = (By.CSS_SELECTOR, '[role="alert"]')

    def wait_page_loaded(self) -> str:
        """Wait for the doctor detail booking section to render."""
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )
        self.wait_visible(self.DOCTOR_NAME)
        self.wait_visible(self.SCHEDULE_HEADING)
        return self.current_url

    def get_available_slots(self) -> list[WebElement]:
        """Return visible, enabled schedule buttons without clicking them."""
        return [
            element
            for element in self.driver.find_elements(*self.AVAILABLE_SLOTS)
            if element.is_displayed() and element.is_enabled()
        ]

    def _wait_slot_containing(self, text: str) -> WebElement:
        """Wait for an enabled schedule button containing the supplied text."""
        def find_slot(driver):
            for element in driver.find_elements(*self.AVAILABLE_SLOTS):
                if element.is_displayed() and element.is_enabled() and text in element.text:
                    return element
            return False

        return self.wait.until(find_slot)

    def select_date(self, date_text: str) -> None:
        """Select an available schedule by its displayed work date."""
        self._wait_slot_containing(date_text).click()

    def select_time_slot(self, time_slot: str) -> None:
        """Select an available schedule by its displayed time label."""
        self._wait_slot_containing(time_slot).click()

    def fill_booking_note(self, note: str | None) -> None:
        """Fill the optional booking note without exposing sensitive data."""
        if note is not None:
            self.type_text(self.NOTE_INPUT, note)

    def submit_booking(self) -> None:
        """Submit the selected booking and wait for a route or error response."""
        self.wait_clickable(self.SUBMIT_BUTTON).click()
        self.wait.until(self._submission_finished)

    def _submission_finished(self, driver) -> bool:
        """Return when the booking request navigates or exposes an error."""
        if urlparse(driver.current_url).path.rstrip("/") == self.APPOINTMENTS_ROUTE:
            return True
        for element in driver.find_elements(*self.ERROR_ALERT):
            if element.is_displayed():
                logger.warning("Booking submission displayed an error alert")
                return True
        return False

    def wait_booking_success(self) -> str:
        """Wait for the successful appointments route and heading."""
        def success(driver):
            on_appointments = (
                urlparse(driver.current_url).path.rstrip("/")
                == self.APPOINTMENTS_ROUTE
            )
            if on_appointments:
                return self.current_url
            heading_visible = any(
                element.is_displayed()
                for element in driver.find_elements(*self.SUCCESS_HEADING)
            )
            return self.current_url if heading_visible else False

        try:
            return self.wait.until(success)
        except TimeoutException as exc:
            if self.get_error_alert_if_present() is not None:
                raise TimeoutException(
                    "Booking submission did not succeed because an error alert was displayed"
                ) from exc
            raise TimeoutException(
                "Booking submission did not reach the appointments page"
            ) from exc

    def get_error_alert_if_present(self) -> WebElement | None:
        """Return a visible booking error without exposing credential data."""
        for element in self.driver.find_elements(*self.ERROR_ALERT):
            if element.is_displayed():
                return element
        return None
