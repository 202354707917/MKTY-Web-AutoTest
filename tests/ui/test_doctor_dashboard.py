"""Read-only UI checks for the doctor dashboard."""

from urllib.parse import urlparse

import pytest
from selenium.webdriver.support.ui import WebDriverWait

from pages.doctor_dashboard_page import DoctorDashboardPage
from pages.login_page import LoginPage


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_doctor_can_access_dashboard(driver, doctor_credentials):
    """A configured doctor account can access the doctor dashboard."""
    username, password = doctor_credentials
    driver.get("http://localhost:8088/login")

    login_page = LoginPage(driver)
    login_page.wait_for_heading()
    login_page.enter_username(username)
    login_page.enter_password(password)
    login_page.submit()
    WebDriverWait(driver, 10).until(
        lambda current_driver: urlparse(current_driver.current_url).path.rstrip("/")
        == "/doctor"
    )

    dashboard = DoctorDashboardPage(driver)
    dashboard.wait_for_route()
    dashboard.wait_page_loaded()

    assert dashboard.get_page_title(), "Doctor dashboard title is empty"
    statistics = dashboard.get_statistics()
    assert set(statistics) == set(dashboard.STAT_LABELS)
    assert dashboard.is_dashboard_visible(), "Doctor dashboard is not visible"
