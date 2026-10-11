"""Page object for the patient's doctor search page."""

from urllib.parse import urljoin, urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from pages.base_page import BasePage


class PatientDoctorPage(BasePage):
    """Expose read-only checks for the patient doctor search page."""

    ROUTE = "/patient/doctors"
    HEADING = (By.XPATH, "//h2[normalize-space()='医生列表']")
    SEARCH_INPUT = (
        By.CSS_SELECTOR,
        'input[placeholder="搜索医生姓名 / 擅长"]',
    )
    EMPTY_STATE = (By.XPATH, "//h3[normalize-space()='没有匹配的医生']")
    LOAD_ERROR = (By.CSS_SELECTOR, '[role="alert"]')
    DOCTOR_CARDS = (
        By.XPATH,
        "//main//div[contains(@class, 'text-lg') and contains(@class, 'font-semibold')]",
    )
    DOCTOR_DETAIL_LINKS = (
        By.CSS_SELECTOR,
        'a[href^="/patient/doctors/"]',
    )

    def __init__(
        self,
        driver,
        base_url: str = "http://localhost:8088",
        timeout: int = 10,
    ) -> None:
        super().__init__(driver, timeout)
        self.base_url = base_url.rstrip("/")

    def open_doctor_search(self) -> None:
        """Open the patient doctor search route."""
        self.open(f"{self.base_url}{self.ROUTE}")

    def wait_for_route(self) -> str:
        """Wait until the browser reaches the doctor search route."""
        self.wait.until(
            lambda driver: urlparse(driver.current_url).path.rstrip("/")
            == self.ROUTE
        )
        return self.current_url

    def wait_for_heading(self) -> WebElement:
        """Wait for the doctor list heading."""
        return self.wait_visible(self.HEADING)

    def wait_for_search_input(self) -> WebElement:
        """Wait for the doctor search input."""
        return self.wait_visible(self.SEARCH_INPUT)

    def enter_search(self, keyword: str) -> None:
        """Enter a non-secret doctor search term without submitting a form."""
        self.type_text(self.SEARCH_INPUT, keyword)

    def find_doctor_cards(self) -> list[WebElement]:
        """Return visible doctor name elements without interacting with cards."""
        return [
            element
            for element in self.driver.find_elements(*self.DOCTOR_CARDS)
            if element.is_displayed()
        ]

    def find_doctor_detail_links(self) -> list[WebElement]:
        """Return visible links to doctor detail pages without clicking them."""
        return [
            element
            for element in self.driver.find_elements(*self.DOCTOR_DETAIL_LINKS)
            if element.is_displayed()
        ]

    def get_first_doctor_detail_url(self) -> str:
        """Return the complete URL of the first visible doctor detail link."""
        links = self.find_doctor_detail_links()
        if not links:
            raise RuntimeError("No visible doctor detail link was found")

        href = links[0].get_attribute("href")
        if not href:
            raise RuntimeError("The first doctor detail link has no destination URL")
        return urljoin(self.base_url + "/", href)

    def open_first_doctor_detail(self) -> None:
        """Open the first doctor detail route directly by its link URL."""
        self.driver.get(self.get_first_doctor_detail_url())

    def wait_for_list_state(self) -> str:
        """Wait until doctor records or the confirmed empty state is visible."""
        def state(driver):
            if any(
                element.is_displayed()
                for element in driver.find_elements(*self.EMPTY_STATE)
            ):
                return "empty"
            if any(
                element.is_displayed()
                for element in driver.find_elements(*self.DOCTOR_CARDS)
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
                "Doctor list did not show records or the empty state." + diagnostic
            ) from exc

    def wait_for_empty_state(self) -> WebElement:
        """Wait for the confirmed no-match message."""
        return self.wait_visible(self.EMPTY_STATE)
