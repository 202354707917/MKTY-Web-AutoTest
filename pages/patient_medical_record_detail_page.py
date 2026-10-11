"""Page object for a patient's medical record detail page."""

from urllib.parse import urlparse

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class PatientMedicalRecordDetailPage(BasePage):
    """Expose read-only fields on the medical record detail page."""

    ROUTE_PREFIX = "/patient/records/"
    HEADING = (By.XPATH, "//main//h2[normalize-space()='病历详情']")
    DOCTOR_LABEL = (By.XPATH, "//main//*[normalize-space()='医生']")
    APPOINTMENT_LABEL = (By.XPATH, "//main//*[normalize-space()='关联预约']")
    VISIT_DATE_LABEL = (By.XPATH, "//main//*[normalize-space()='就诊日期']")
    DIAGNOSIS_LABEL = (By.XPATH, "//main//*[normalize-space()='诊断']")

    def open_detail(self, url: str) -> None:
        """Open the supplied medical record detail URL."""
        self.open(url)

    def wait_for_route(self) -> str:
        """Wait until the browser reaches a record detail route."""
        self.wait.until(
            lambda driver: (
                urlparse(driver.current_url).path.startswith(self.ROUTE_PREFIX)
                and urlparse(driver.current_url).path.rstrip("/")
                != self.ROUTE_PREFIX.rstrip("/")
            )
        )
        return self.current_url

    def wait_page_loaded(self) -> str:
        """Wait for the detail heading and stable core field labels."""
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )
        self.wait_visible(self.HEADING)
        self.wait_visible(self.DOCTOR_LABEL)
        self.wait_visible(self.DIAGNOSIS_LABEL)
        return self.current_url

    def get_title(self) -> str:
        """Return the visible medical record detail title."""
        return self.wait_visible(self.HEADING).text.strip()

    def is_detail_visible(self) -> bool:
        """Return whether the title and core record fields are visible."""
        try:
            self.wait_visible(self.HEADING)
            self.wait_visible(self.DOCTOR_LABEL)
            self.wait_visible(self.APPOINTMENT_LABEL)
            self.wait_visible(self.VISIT_DATE_LABEL)
            self.wait_visible(self.DIAGNOSIS_LABEL)
            return True
        except Exception:
            return False
