"""Read-only UI checks for the patient appointments page."""

import pytest

from pages.patient_appointments_page import PatientAppointmentsPage
from pages.patient_entry_page import PatientEntryPage


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_patient_appointments_page_loads(authenticated_driver):
    """A configured patient account should see the appointments page shell."""
    driver = authenticated_driver
    patient_entry = PatientEntryPage(driver)
    patient_entry.open_patient_portal()
    patient_entry.wait_for_appointments_navigation()

    appointments_page = PatientAppointmentsPage(driver)
    appointments_page.open_appointments()
    appointments_page.wait_for_route()

    heading = appointments_page.wait_for_heading()
    all_status_tab = appointments_page.wait_for_all_status_tab()

    assert heading.is_displayed(), "Patient appointments heading is not visible"
    assert all_status_tab.is_displayed(), (
        "All-status appointments filter is not visible"
    )


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_patient_appointments_list_reaches_read_only_state(authenticated_driver):
    """The appointments list should settle into records or empty state."""
    driver = authenticated_driver
    patient_entry = PatientEntryPage(driver)
    patient_entry.open_patient_portal()
    patient_entry.wait_for_appointments_navigation()

    appointments_page = PatientAppointmentsPage(driver)
    appointments_page.open_appointments()
    appointments_page.wait_for_route()
    state = appointments_page.wait_for_list_state()

    assert state in {"records", "empty"}, (
        f"Unexpected appointments list state: {state!r}"
    )
    if state == "records":
        rows = appointments_page.find_appointment_rows()
        assert rows, "Appointments list reported records but no visible rows were found"
    elif state == "empty":
        empty_state = appointments_page.wait_for_empty_state()
        assert empty_state.text.strip() == "暂无预约", (
            f"Unexpected empty appointments message: {empty_state.text!r}"
        )
