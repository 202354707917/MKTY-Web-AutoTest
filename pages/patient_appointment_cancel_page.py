"""Page object for cancelling an existing patient appointment."""

from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from pages.patient_appointments_page import PatientAppointmentsPage


class PatientAppointmentCancelPage(PatientAppointmentsPage):
    """Expose the guarded, visible cancellation interaction."""

    CANCELLABLE_CARDS = (
        By.XPATH,
        "//main//div[contains(@class, 'premium-card')]"
        "[.//button[normalize-space()='取消预约']]",
    )
    CANCEL_BUTTON = (By.XPATH, ".//button[normalize-space()='取消预约']")
    CANCELLED_STATUS = (
        By.XPATH,
        ".//span[contains(@class, 'inline-flex') and normalize-space()='已取消']",
    )

    def find_cancellable_appointments(self) -> list[str]:
        """Return stable labels for visible cards with a cancel action."""
        labels: list[str] = []
        for card in self.driver.find_elements(*self.CANCELLABLE_CARDS):
            try:
                if card.is_displayed():
                    labels.append(self._read_appointment_label(card))
            except StaleElementReferenceException:
                continue
        return labels

    @staticmethod
    def _read_appointment_label(card: WebElement) -> str:
        """Read a card label immediately while its element is current."""
        return card.find_element(By.XPATH, ".//h3[1]").text.strip()

    def find_cancelable_appointment(self) -> str | None:
        """Return the first pending appointment label, if one is available."""
        labels = self.find_cancellable_appointments()
        return labels[0] if labels else None

    def _diagnostic_context(self) -> str:
        """Return safe browser diagnostics without credential data."""
        try:
            current_url = self.driver.current_url
        except Exception:
            current_url = "<unavailable>"
        try:
            title = self.driver.title
        except Exception:
            title = "<unavailable>"
        return f"Current URL: {current_url}; page title: {title}"

    @staticmethod
    def _xpath_literal(value: str) -> str:
        """Encode a UI label as an XPath string literal."""
        if "'" not in value:
            return f"'{value}'"
        parts = value.split("'")
        args: list[str] = []
        for index, part in enumerate(parts):
            args.append(f"'{part}'")
            if index < len(parts) - 1:
                args.append('"\'"')
        return "concat(" + ", ".join(args) + ")"

    def _cancel_button_locator(self, appointment_label: str) -> tuple[str, str]:
        """Build a locator that re-finds the current cancel button in the card."""
        label = self._xpath_literal(appointment_label)
        return (
            By.XPATH,
            "//main//div[contains(@class, 'premium-card')]"
            f"[.//h3[1][normalize-space()={label}]]"
            "//button[normalize-space()='取消预约']",
        )

    def retry_click_cancel_button(self, appointment_label: str) -> None:
        """Re-find and click the cancel button, retrying one stale click once."""
        locator = self._cancel_button_locator(appointment_label)
        for attempt in range(2):
            try:
                self.wait.until(EC.element_to_be_clickable(locator)).click()
                return
            except StaleElementReferenceException as exc:
                if attempt == 1:
                    raise StaleElementReferenceException(
                        "Cancel button became stale after two fresh lookups. "
                        + self._diagnostic_context()
                    ) from exc

    def cancel_appointment(self, appointment_label: str) -> None:
        """Confirm cancellation through the current browser dialog."""
        self.retry_click_cancel_button(appointment_label)
        self.wait.until(EC.alert_is_present())
        self.driver.switch_to.alert.accept()

    def wait_for_cancelled_status(self, appointment_label: str) -> str:
        """Re-find the card until it displays the 已取消 status text."""
        def find_cancelled_card(driver):
            for card in driver.find_elements(*self.APPOINTMENT_RECORDS):
                try:
                    if not card.is_displayed() or appointment_label not in card.text:
                        continue
                    for status in card.find_elements(*self.CANCELLED_STATUS):
                        if status.is_displayed():
                            return status.text.strip()
                except StaleElementReferenceException:
                    continue
            return False

        try:
            return self.wait.until(find_cancelled_card)
        except TimeoutException as exc:
            raise TimeoutException(
                "The appointment did not reach the 已取消 state. "
                + self._diagnostic_context()
            ) from exc
