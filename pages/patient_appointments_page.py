"""Page object for the patient's appointments page."""

from urllib.parse import urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from pages.base_page import BasePage


class PatientAppointmentsPage(BasePage):
    """Expose read-only patient appointments page checks."""

    ROUTE = "/patient/appointments"
    HEADING = (By.XPATH, "//h2[normalize-space()='我的预约']")
    ALL_STATUS_TAB = (By.XPATH, "//button[normalize-space()='全部']")
    EMPTY_STATE = (By.XPATH, "//h3[normalize-space()='暂无预约']")
    LOAD_ERROR = (By.CSS_SELECTOR, '[role="alert"]')
    APPOINTMENT_ROWS = (
        By.XPATH,
        "//main//h3[not(normalize-space()='暂无预约')]",
    )
    APPOINTMENT_RECORDS = (
        By.XPATH,
        "//main//div[contains(@class, 'premium-card')][.//h3 and not(.//h3[normalize-space()='暂无预约'])]",
    )

    def open_appointments(self, base_url: str = "http://localhost:8088") -> None:
        """Open the appointments route directly without clicking SPA navigation."""
        self.open(f"{base_url.rstrip('/')}{self.ROUTE}")

    def wait_for_route(self) -> str:
        """Wait until the browser reaches the appointments route."""
        self.wait.until(
            lambda driver: urlparse(driver.current_url).path.rstrip("/")
            == self.ROUTE
        )
        return self.current_url

    def wait_for_heading(self) -> WebElement:
        """Wait for the appointments page heading."""
        return self.wait_visible(self.HEADING)

    def wait_for_all_status_tab(self) -> WebElement:
        """Wait for the all-status filter button."""
        return self.wait_visible(self.ALL_STATUS_TAB)

    def wait_for_list_state(self) -> str:
        """Wait until records or a confirmed empty state is visible."""
        def state(driver):
            if any(element.is_displayed() for element in driver.find_elements(*self.EMPTY_STATE)):
                return "empty"
            if any(element.is_displayed() for element in driver.find_elements(*self.APPOINTMENT_ROWS)):
                return "records"
            return False

        try:
            return self.wait.until(state)
        except TimeoutException as exc:
            error_visible = any(
                element.is_displayed()
                for element in self.driver.find_elements(*self.LOAD_ERROR)
            )
            diagnostic = " A load error alert was visible." if error_visible else ""
            raise TimeoutException(
                "Appointments page did not show records or the empty state."
                + diagnostic
            ) from exc

    def find_appointment_rows(self) -> list[WebElement]:
        """Return visible appointment record headings without interacting with them."""
        return [
            element
            for element in self.driver.find_elements(*self.APPOINTMENT_ROWS)
            if element.is_displayed()
        ]

    def get_appointment_records(self) -> list[dict[str, str]]:
        """Read visible appointment cards without interacting with controls."""
        records: list[dict[str, str]] = []
        for card in self.driver.find_elements(*self.APPOINTMENT_RECORDS):
            if not card.is_displayed():
                continue
            heading = card.find_element(By.XPATH, ".//h3[1]").text.strip()
            department, separator, doctor = heading.partition(" · ")
            if not separator:
                department, doctor = "", heading
            doctor = doctor.split("（", 1)[0].strip()
            status_elements = card.find_elements(
                By.CSS_SELECTOR,
                "span.inline-flex",
            )
            time_elements = card.find_elements(
                By.XPATH,
                ".//p[contains(@class, 'mt-2') and contains(@class, 'text-sm')][1]",
            )
            records.append(
                {
                    "doctor": doctor.strip(),
                    "department": department.strip(),
                    "time": time_elements[0].text.strip() if time_elements else "",
                    "status": status_elements[0].text.strip() if status_elements else "",
                }
            )
        return records

    def get_first_appointment(self) -> dict[str, str] | None:
        """Return the first visible appointment record, if present."""
        records = self.get_appointment_records()
        return records[0] if records else None

    def has_appointment(self) -> bool:
        """Return whether at least one visible appointment record exists."""
        return bool(self.get_appointment_records())

    def wait_for_empty_state(self) -> WebElement:
        """Wait for the confirmed empty appointments message."""
        return self.wait_visible(self.EMPTY_STATE)

    def wait_for_load_error(self) -> WebElement:
        """Wait for the appointments load error region."""
        return self.wait_visible(self.LOAD_ERROR)
