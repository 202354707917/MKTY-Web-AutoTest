"""Page object for doctors filtered by a patient department."""

from urllib.parse import parse_qs, urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class PatientDoctorFilterPage(BasePage):
    """Expose read-only checks for a department-filtered doctor list."""

    ROUTE = "/patient/doctors"
    HEADING = (By.XPATH, "//main//h2[normalize-space()='医生列表']")
    DEPARTMENT_SELECT = (By.CSS_SELECTOR, "select")
    DOCTOR_NAMES = (
        By.XPATH,
        "//main//div[contains(@class, 'text-lg') and contains(@class, 'font-semibold')]",
    )
    EMPTY_STATE = (By.XPATH, "//main//h3[normalize-space()='没有匹配的医生']")
    LOAD_ERROR = (By.CSS_SELECTOR, "[role='alert']")

    def open_filtered_doctors(self, url: str) -> None:
        """Open the supplied department-filtered doctor URL directly."""
        self.open(url)

    def wait_for_route(self) -> str:
        """Wait for the doctors route with a non-empty departmentId query."""
        def matches(driver):
            parsed = urlparse(driver.current_url)
            query = parse_qs(parsed.query)
            return (
                parsed.path.rstrip("/") == self.ROUTE
                and bool(query.get("departmentId", [""])[0])
            )

        self.wait.until(matches)
        return self.current_url

    def wait_page_loaded(self) -> str:
        """Wait for the filtered doctor page heading and department selector."""
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )
        self.wait_visible(self.HEADING)
        self.wait_visible(self.DEPARTMENT_SELECT)
        return self.current_url

    def get_current_department(self) -> str:
        """Return the selected department label from the current selector."""
        select = self.wait_visible(self.DEPARTMENT_SELECT)
        selected = select.find_elements(By.CSS_SELECTOR, "option:checked")
        return selected[0].text.strip() if selected else ""

    def get_doctor_names(self) -> list[str]:
        """Return visible doctor card headings without caching elements."""
        return [
            element.text.strip()
            for element in self.driver.find_elements(*self.DOCTOR_NAMES)
            if element.is_displayed() and element.text.strip()
        ]

    def get_doctor_count(self) -> int:
        """Return the number of visible doctor card headings."""
        return len(self.get_doctor_names())

    def is_empty_state_visible(self) -> bool:
        """Return whether the confirmed no-match state is visible."""
        return any(
            element.is_displayed()
            for element in self.driver.find_elements(*self.EMPTY_STATE)
        )

    def wait_for_list_state(self) -> str:
        """Wait until filtered doctors or the confirmed empty state appears."""
        def state(driver):
            if any(
                element.is_displayed()
                for element in driver.find_elements(*self.EMPTY_STATE)
            ):
                return "empty"
            if any(
                element.is_displayed()
                for element in driver.find_elements(*self.DOCTOR_NAMES)
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
                "Filtered doctor list did not show doctors or the empty state."
                + diagnostic
            ) from exc
