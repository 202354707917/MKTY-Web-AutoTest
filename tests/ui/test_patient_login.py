"""Read-only UI test for successful patient login."""

import pytest

from pages.login_page import LoginPage
from pages.patient_entry_page import PatientEntryPage


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_patient_login_reaches_patient_center(driver, login_credentials):
    """A configured patient account should reach the patient center."""
    username, password = login_credentials
    patient_page = PatientEntryPage(driver)
    patient_page.open_patient_portal()
    patient_page.wait_for_login_redirect()

    login_page = LoginPage(driver)
    login_page.wait_for_heading()
    login_page.enter_username(username)
    login_page.enter_password(password)
    login_page.submit()
    login_page.wait_for_patient_route()

    heading = patient_page.wait_for_patient_center_heading()
    appointments_nav = patient_page.wait_for_appointments_navigation()

    assert heading.is_displayed(), "Patient center heading is not visible"
    assert appointments_nav.is_displayed(), (
        "Patient appointments navigation is not visible"
    )
