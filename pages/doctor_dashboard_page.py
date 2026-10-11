"""Page object for the doctor's read-only dashboard."""

from urllib.parse import urlparse

from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class DoctorDashboardPage(BasePage):
    """Expose stable, read-only checks for the doctor dashboard."""

    ROUTE = "/doctor"
    HEADING = (
        By.XPATH,
        "//main//h2[contains(normalize-space(), '医生，欢迎回来')]",
    )
    STAT_LABELS = ("今日预约", "待接诊", "已完成病历")
    STAT_VALUES = {
        "今日预约": (By.XPATH, "//main//p[normalize-space()='今日预约']/following-sibling::p[1]"),
        "待接诊": (By.XPATH, "//main//p[normalize-space()='待接诊']/following-sibling::p[1]"),
        "已完成病历": (By.XPATH, "//main//p[normalize-space()='已完成病历']/following-sibling::p[1]"),
    }
    EMPTY_STATE = (By.XPATH, "//main//h3[normalize-space()='未绑定医生档案']")
    LOAD_ERROR = (By.CSS_SELECTOR, "[role='alert']")

    def open_doctor_portal(self, base_url: str = "http://localhost:8088") -> str:
        """Open the doctor dashboard route directly."""
        self.open(f"{base_url.rstrip('/')}{self.ROUTE}")
        return self.current_url

    def wait_for_route(self) -> str:
        """Wait until the browser reaches the doctor dashboard route."""
        self.wait.until(
            lambda driver: urlparse(driver.current_url).path.rstrip("/")
            == self.ROUTE
        )
        return self.current_url

    def wait_page_loaded(self) -> str:
        """Wait for the dashboard heading and statistics to render."""
        self.wait.until(
            lambda driver: driver.execute_script("return document.readyState")
            == "complete"
        )
        self.wait_visible(self.HEADING)
        for label in self.STAT_LABELS:
            self.wait_visible(self.STAT_VALUES[label])
        return self.current_url

    def get_page_title(self) -> str:
        """Return the dynamic doctor dashboard heading."""
        return self.wait_visible(self.HEADING).text.strip()

    def get_statistics(self) -> dict[str, str]:
        """Return displayed dashboard statistic values keyed by their labels."""
        return {
            label: self.wait_visible(self.STAT_VALUES[label]).text.strip()
            for label in self.STAT_LABELS
        }

    def is_dashboard_visible(self) -> bool:
        """Return whether the title and all dashboard statistics are visible."""
        try:
            self.wait_visible(self.HEADING)
            self.get_statistics()
            return True
        except Exception:
            return False
