"""Read-only UI checks for the patient profile page."""

import pytest

from pages.patient_profile_page import PatientProfilePage


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_patient_profile_page_displays_account_information(authenticated_driver):
    """An authenticated patient can view the profile information page."""
    profile_page = PatientProfilePage(authenticated_driver)
    profile_page.open_profile()
    profile_page.wait_for_route()
    profile_page.wait_page_loaded()

    assert profile_page.is_profile_visible(), (
        "Patient profile title and identity fields are not visible"
    )
    assert profile_page.get_username(), "Patient profile username is empty"
    assert profile_page.get_role(), "Patient profile role is empty"
    profile_info = profile_page.get_profile_info()
    assert profile_info["name"], "Patient profile name is empty"
    assert profile_info["phone"], "Patient profile phone is empty"
