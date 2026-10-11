"""Page object for the patient's department selection page."""

from urllib.parse import urljoin, urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class PatientDepartmentPage(BasePage):
    """Expose read-only department list checks."""

    ROUTE = "/patient/departments"
    HEADING = (By.XPATH, "//main//h2[normalize-space()='选择科室']")
    EMPTY_STATE = (By.XPATH, "//main//h3[normalize-space()='暂无科室']")
    LOAD_ERROR = (By.CSS_SELECTOR, "[role='alert']")
    DEPARTMENT_LINKS = (
        By.CSS_SELECTOR,
        "a[href^='/patient/doctors?departmentId=']",
    )
    DEPARTMENT_NAMES = (
        By.CSS_SELECTOR,
        "a[href^='/patient/doctors?departmentId='] h3",
    )

    def __init__(
        self,
        driver,
        base_url: str = "http://localhost:8088",
        timeout: int = 10,
    ) -> None:
        super().__init__(driver, timeout)
        self.base_url = base_url.rstrip("/")

    def open_departments(self) -> None:
        """Open the patient department selection route directly."""
        self.open(f"{self.base_url}{self.ROUTE}")

    def wait_for_route(self) -> str:
        """Wait until the browser reaches the department route."""
        self.wait.until(
            lambda driver: urlparse(driver.current_url).path.rstrip("/")
            == self.ROUTE
        )
        return self.current_url

    def wait_page_loaded(self) -> str:
        """Wait for document readiness and the department page heading."""
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )
        self.wait_visible(self.HEADING)
        return self.current_url

    def wait_for_list_state(self) -> str:
        """Wait until department links or the confirmed empty state is visible."""
        def state(driver):
            if any(
                element.is_displayed()
                for element in driver.find_elements(*self.EMPTY_STATE)
            ):
                return "empty"
            if any(
                element.is_displayed()
                for element in driver.find_elements(*self.DEPARTMENT_NAMES)
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
                "Department page did not show departments or the empty state."
                + diagnostic
            ) from exc

    def get_department_names(self) -> list[str]:
        """Return visible department names without exposing WebElements."""
        return [
            element.text.strip()
            for element in self.driver.find_elements(*self.DEPARTMENT_NAMES)
            if element.is_displayed() and element.text.strip()
        ]

    def get_first_department_detail_url(self) -> str:
        """Return the first department's doctor-list URL."""
        return self.get_first_department_filter_url()

    def get_first_department_filter_url(self) -> str:
        """Return the first department's complete filtered-doctor URL."""
        for element in self.driver.find_elements(*self.DEPARTMENT_LINKS):
            if not element.is_displayed():
                continue
            href = element.get_attribute("href")
            if href:
                return urljoin(self.base_url + "/", href)
        raise RuntimeError("No department doctor-list link was found")

    def is_empty_state_visible(self) -> bool:
        """Return whether the confirmed empty department message is visible."""
        return any(
            element.is_displayed()
            for element in self.driver.find_elements(*self.EMPTY_STATE)
        )
