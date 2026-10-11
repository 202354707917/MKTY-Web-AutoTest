"""Page object for the doctor's read-only appointment/record detail view."""

import re
from urllib.parse import urlparse

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class DoctorAppointmentDetailPage(BasePage):
    """Read fields rendered by the doctor's appointment detail route."""

    ROUTE_PATTERN = re.compile(r"^/doctor/appointments/[^/]+/record/?$")
    HEADING = (By.XPATH, "//main//h2[normalize-space()='书写电子病历' or normalize-space()='病历详情']")
    DETAIL_PANEL = (By.XPATH, "//main//div[contains(@class, 'premium-card')]")
    PATIENT_SUMMARY = (By.XPATH, "//main//h2/following-sibling::p[1]")
    APPOINTMENT_NUMBER = (By.XPATH, "//main//*[contains(normalize-space(), '预约单号：')]")
    DEPARTMENT = (By.XPATH, "//main//*[contains(normalize-space(), '科室：')]")
    SYMPTOM = (By.XPATH, "//main//*[contains(normalize-space(), '症状备注：')]")
    LOAD_ERROR = (By.CSS_SELECTOR, "[role='alert']")
    EMPTY_STATE = (By.XPATH, "//main//h3[normalize-space()='预约不存在']")

    def open_detail(self, detail_url: str) -> str:
        """Open a previously discovered appointment detail URL."""
        self.open(detail_url)
        return self.current_url

    def wait_for_route(self) -> str:
        """Wait until the dynamic appointment detail route is active."""
        self.wait.until(
            lambda driver: bool(self.ROUTE_PATTERN.match(urlparse(driver.current_url).path))
        )
        return self.current_url

    def wait_page_loaded(self) -> str:
        """Wait for the detail page heading and appointment information to render."""
        self.wait_visible(self.HEADING)
        self.wait_visible(self.PATIENT_SUMMARY)
        self.wait_visible(self.DEPARTMENT)
        return self.current_url

    def get_appointment_details(self) -> dict[str, str]:
        """Return visible appointment detail text without exposing WebElements."""
        summary = self.wait_visible(self.PATIENT_SUMMARY).text.strip()
        summary_parts = [part.strip() for part in summary.split("·")]
        patient = summary_parts[0].removeprefix("患者").strip()
        return {
            "title": self.wait_visible(self.HEADING).text.strip(),
            "patient": patient,
            "summary": summary,
            "appointment_time": " · ".join(summary_parts[1:]),
            "appointment_number": self.wait_visible(self.APPOINTMENT_NUMBER).text.strip(),
            "department": self.wait_visible(self.DEPARTMENT).text.strip(),
            "symptom": next(
                (
                    element.text.strip()
                    for element in self.driver.find_elements(*self.SYMPTOM)
                    if element.is_displayed()
                ),
                "",
            ),
        }

    def is_detail_visible(self) -> bool:
        """Return whether the appointment detail content is visible."""
        try:
            self.wait_page_loaded()
            return True
        except Exception:
            return False
