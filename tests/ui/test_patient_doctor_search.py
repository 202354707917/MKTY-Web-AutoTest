"""Read-only UI checks for the patient doctor search page."""

import pytest

from pages.patient_doctor_page import PatientDoctorPage
from pages.patient_entry_page import PatientEntryPage


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_patient_doctor_search_reaches_read_only_state(authenticated_driver):
    """The doctor list should settle into records or an explicit empty state."""
    driver = authenticated_driver
    patient_entry = PatientEntryPage(driver)
    patient_entry.open_patient_portal()

    doctor_page = PatientDoctorPage(driver)
    doctor_page.open_doctor_search()
    doctor_page.wait_for_route()
    doctor_page.wait_for_heading()
    doctor_page.wait_for_search_input()

    state = doctor_page.wait_for_list_state()
    assert state in {"records", "empty"}, (
        f"Unexpected doctor list state: {state!r}"
    )
    if state == "records":
        assert doctor_page.find_doctor_cards(), (
            "Doctor list reported records but no visible doctor cards were found"
        )
    else:
        empty_state = doctor_page.wait_for_empty_state()
        assert empty_state.text.strip() == "没有匹配的医生", (
            f"Unexpected doctor list empty message: {empty_state.text!r}"
        )
