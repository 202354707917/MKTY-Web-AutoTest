"""Page object for the patient's medical record list."""

from urllib.parse import urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from pages.base_page import BasePage


class PatientMedicalRecordPage(BasePage):
    """Expose read-only checks for the patient medical record page."""

    ROUTE = "/patient/records"
    HEADING = (By.XPATH, "//main//h2[normalize-space()='我的病历']")
    EMPTY_STATE = (By.XPATH, "//main//h3[normalize-space()='暂无病历']")
    LOAD_ERROR = (By.CSS_SELECTOR, "[role='alert']")
    RECORD_CARDS = (
        By.XPATH,
        "//main//div[contains(@class, 'premium-card')][.//h3]",
    )
    DETAIL_LINKS = (By.CSS_SELECTOR, "a[href^='/patient/records/']")

    def open_medical_records(self, base_url: str = "http://localhost:8088") -> None:
        """Open the patient medical record route directly."""
        self.open(f"{base_url.rstrip('/')}{self.ROUTE}")

    def wait_for_route(self) -> str:
        """Wait until the browser reaches the medical record route."""
        self.wait.until(
            lambda driver: urlparse(driver.current_url).path.rstrip("/")
            == self.ROUTE
        )
        return self.current_url

    def wait_page_loaded(self) -> str:
        """Wait for document readiness and the medical record heading."""
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )
        self.wait_visible(self.HEADING)
        return self.current_url

    def wait_for_list_state(self) -> str:
        """Wait until records or the confirmed empty state is visible."""
        def state(driver):
            if any(
                element.is_displayed()
                for element in driver.find_elements(*self.EMPTY_STATE)
            ):
                return "empty"
            if any(
                element.is_displayed()
                for element in driver.find_elements(*self.RECORD_CARDS)
            ):
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
                "Medical record list did not show records or the empty state."
                + diagnostic
            ) from exc

    def is_empty_state_visible(self) -> bool:
        """Return whether the confirmed empty-state message is visible."""
        return any(
            element.is_displayed()
            for element in self.driver.find_elements(*self.EMPTY_STATE)
        )

    def get_first_record(self) -> dict[str, str] | None:
        """Read the first visible record card without retaining its element."""
        for card in self.driver.find_elements(*self.RECORD_CARDS):
            if not card.is_displayed():
                continue
            heading = card.find_element(By.XPATH, ".//h3[1]").text.strip()
            department, separator, doctor = heading.partition(" · ")
            if not separator:
                department, doctor = "", heading
            detail = card.find_elements(
                By.CSS_SELECTOR,
                "a[href^='/patient/records/']",
            )
            date_line = card.find_elements(
                By.XPATH,
                ".//p[contains(@class, 'mt-1')][1]",
            )
            diagnosis_line = card.find_elements(
                By.XPATH,
                ".//p[contains(normalize-space(), '诊断：')][1]",
            )
            return {
                "department": department.strip(),
                "doctor": doctor.strip(),
                "date": date_line[0].text.strip() if date_line else "",
                "diagnosis": diagnosis_line[0].text.strip() if diagnosis_line else "",
                "has_detail_link": "yes" if detail else "no",
            }
        return None

    def find_detail_links(self) -> list[str]:
        """Return detail href values without exposing WebElements to callers."""
        return [
            href
            for element in self.driver.find_elements(*self.DETAIL_LINKS)
            if element.is_displayed()
            for href in [element.get_attribute("href")]
            if href
        ]

    def get_first_record_detail_url(self) -> str:
        """Return the first record's stable detail URL."""
        links = self.find_detail_links()
        if not links:
            raise RuntimeError("No medical record detail link was found")
        return links[0]
