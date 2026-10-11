"""Page object for the doctor's read-only appointment list."""

from urllib.parse import urljoin, urlparse

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class DoctorAppointmentsPage(BasePage):
    """Read appointment data rendered by the doctor portal."""

    ROUTE = "/doctor/appointments"
    STATUS_FILTERS = {
        "待接诊": "待就诊",
        "已完成": "已就诊",
        "全部": None,
    }
    HEADING = (By.XPATH, "//main//h2[normalize-space()='接诊列表']")
    EMPTY_STATE = (By.XPATH, "//main//h3[normalize-space()='暂无预约']")
    LOAD_ERROR = (By.CSS_SELECTOR, "[role='alert']")
    APPOINTMENT_CARDS = (
        By.XPATH,
        "//main//div[contains(@class, 'premium-card')][.//h3]",
    )

    def open_doctor_appointments(self, base_url: str = "http://localhost:8088") -> str:
        """Open the appointment list directly."""
        self.open(f"{base_url.rstrip('/')}{self.ROUTE}")
        return self.current_url

    def wait_for_route(self) -> str:
        """Wait until the doctor appointment route is active."""
        self.wait.until(
            lambda driver: urlparse(driver.current_url).path.rstrip("/") == self.ROUTE
        )
        return self.current_url

    def wait_page_loaded(self) -> str:
        """Wait for the appointment list heading to render."""
        self.wait_visible(self.HEADING)
        return self.current_url

    def wait_for_list_state(self) -> str:
        """Wait for appointment records or the explicit empty state."""
        def state(driver):
            if any(element.is_displayed() for element in driver.find_elements(*self.EMPTY_STATE)):
                return "empty"
            if any(element.is_displayed() for element in driver.find_elements(*self.APPOINTMENT_CARDS)):
                return "records"
            return False

        try:
            return self.wait.until(state)
        except TimeoutException as exc:
            error_visible = any(
                element.is_displayed() for element in self.driver.find_elements(*self.LOAD_ERROR)
            )
            detail = " A load error alert is visible." if error_visible else ""
            raise TimeoutException(
                "Doctor appointment list did not show records or '暂无预约'." + detail
            ) from exc

    def select_status_filter(self, label: str) -> str:
        """Select a status tab by its source-defined visible label."""
        if label not in self.STATUS_FILTERS:
            raise ValueError(f"Unsupported doctor appointment status filter: {label!r}")
        locator = (By.XPATH, f"//main//button[normalize-space()='{label}']")
        self.wait.until(lambda driver: self._click_status_filter(locator))
        active_locator = (
            By.XPATH,
            f"//main//button[normalize-space()='{label}' and contains(@class, 'bg-brand-600')]",
        )
        self.wait_visible(active_locator)
        return label

    def _click_status_filter(self, locator: tuple) -> bool:
        """Click a freshly located status button, retrying transient React staleness."""
        try:
            self.wait_clickable(locator).click()
            return True
        except StaleElementReferenceException:
            return False

    def wait_for_filtered_list_state(self, expected_status: str | None) -> str:
        """Wait for an empty list or records matching the selected status label."""
        def state(driver):
            try:
                if any(
                    element.is_displayed()
                    for element in driver.find_elements(*self.EMPTY_STATE)
                ):
                    return "empty"
                cards = [
                    element
                    for element in driver.find_elements(*self.APPOINTMENT_CARDS)
                    if element.is_displayed()
                ]
            except StaleElementReferenceException:
                return False
            if not cards:
                return False
            if expected_status is None:
                return "records"
            try:
                statuses = [
                    card.find_element(By.CSS_SELECTOR, "span.inline-flex").text.strip()
                    for card in cards
                ]
            except StaleElementReferenceException:
                return False
            return "records" if statuses and all(status == expected_status for status in statuses) else False

        return self.wait.until(state)

    def get_appointment_records(self) -> list[dict[str, str]]:
        """Return currently visible appointment card text without interacting with controls."""
        records: list[dict[str, str]] = []
        for card in self.driver.find_elements(*self.APPOINTMENT_CARDS):
            try:
                if not card.is_displayed():
                    continue
                patient_nodes = card.find_elements(By.XPATH, ".//h3[1]")
                status_nodes = card.find_elements(By.CSS_SELECTOR, "span.inline-flex")
                detail_nodes = card.find_elements(
                    By.XPATH,
                    ".//p[contains(@class, 'mt-1') and contains(@class, 'text-sm')][1]",
                )
                note_nodes = card.find_elements(
                    By.XPATH, ".//p[contains(normalize-space(), '主诉备注：')]"
                )
                records.append(
                    {
                        "patient": patient_nodes[0].text.strip() if patient_nodes else "",
                        "status": status_nodes[0].text.strip() if status_nodes else "",
                        "time": detail_nodes[0].text.strip() if detail_nodes else "",
                        "note": note_nodes[0].text.strip() if note_nodes else "",
                    }
                )
            except StaleElementReferenceException:
                continue
        return records

    def get_first_appointment(self) -> dict[str, str] | None:
        """Return the first visible appointment record, if any."""
        records = self.get_appointment_records()
        return records[0] if records else None

    def get_first_appointment_detail_url(self) -> str:
        """Return the first appointment's record/detail URL from the current DOM."""
        for card in self.driver.find_elements(*self.APPOINTMENT_CARDS):
            try:
                if not card.is_displayed():
                    continue
                links = card.find_elements(
                    By.CSS_SELECTOR,
                    "a[href*='/doctor/appointments/'][href$='/record']",
                )
                if links:
                    href = links[0].get_attribute("href")
                    if href:
                        return urljoin(self.current_url, href)
            except StaleElementReferenceException:
                continue
        raise LookupError(
            "No appointment detail link was found in the visible doctor appointment list."
        )

    def is_empty_state_visible(self) -> bool:
        """Return whether the explicit no-appointments message is visible."""
        return any(element.is_displayed() for element in self.driver.find_elements(*self.EMPTY_STATE))
