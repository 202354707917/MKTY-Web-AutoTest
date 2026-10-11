"""Guarded read-after-write UI test for patient booking."""

import pytest

from pages.login_page import LoginPage
from pages.patient_appointments_page import PatientAppointmentsPage
from pages.patient_booking_page import PatientBookingPage
from pages.patient_doctor_detail_page import PatientDoctorDetailPage
from pages.patient_doctor_page import PatientDoctorPage
from pages.patient_entry_page import PatientEntryPage


@pytest.mark.ui
@pytest.mark.write
@pytest.mark.regression
def test_patient_booking_and_verify_appointment(
    booking_test_enabled, driver, login_credentials
):
    """Create one booking and verify its read-only representation."""
    username, password = login_credentials
    patient_entry = PatientEntryPage(driver)
    patient_entry.open_patient_portal()
    patient_entry.wait_for_login_redirect()

    login_page = LoginPage(driver)
    login_page.wait_for_heading()
    login_page.enter_username(username)
    login_page.enter_password(password)
    login_page.submit()
    login_page.wait_for_patient_route()

    doctor_list = PatientDoctorPage(driver)
    doctor_list.open_doctor_search()
    doctor_list.wait_for_route()
    doctor_list.wait_for_heading()
    assert doctor_list.wait_for_list_state() == "records", (
        "A doctor record is required for the booking verification flow"
    )
    doctor_list.open_first_doctor_detail()

    detail_page = PatientDoctorDetailPage(driver)
    detail_page.wait_for_route()
    detail_page.wait_page_loaded()
    doctor_name = detail_page.get_doctor_name()
    selected_slot = detail_page.find_available_schedule()[0]
    slot_lines = [line.strip() for line in selected_slot.text.splitlines() if line.strip()]
    selected_date = slot_lines[0] if slot_lines else ""
    selected_time = slot_lines[1] if len(slot_lines) > 1 else ""
    assert selected_date and selected_time, (
        "Available schedule does not expose date and time text"
    )
    detail_page.select_first_available_schedule()

    booking_page = PatientBookingPage(driver)
    booking_page.wait_page_loaded()
    booking_page.fill_booking_note(None)
    booking_page.submit_booking()
    booking_page.wait_booking_success()

    appointments_page = PatientAppointmentsPage(driver)
    appointments_page.wait_for_route()
    appointments_page.wait_for_heading()
    records = appointments_page.get_appointment_records()
    assert appointments_page.has_appointment(), (
        "The appointments page did not show the newly created appointment"
    )
    matching = [
        record
        for record in records
        if record["doctor"] and record["doctor"] in doctor_name
        and selected_date in record["time"]
        and selected_time in record["time"]
    ]
    assert matching, "The newly created appointment was not found in the read-only list"
    assert matching[0]["department"], "Created appointment has no department information"
    assert matching[0]["status"], "Created appointment has no status information"
