"""Guarded UI test for the patient booking write operation."""

import pytest

from pages.login_page import LoginPage
from pages.patient_booking_page import PatientBookingPage
from pages.patient_doctor_page import PatientDoctorPage
from pages.patient_entry_page import PatientEntryPage


@pytest.mark.ui
@pytest.mark.write
@pytest.mark.regression
def test_patient_booking_flow_disabled_by_default(
    enable_write_test, driver, login_credentials
):
    """Create a booking only when the explicit write-test switch is enabled."""
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
        "A doctor record is required for the guarded booking flow"
    )
    detail_links = doctor_list.find_doctor_detail_links()
    assert detail_links, "No doctor detail link is available for booking setup"
    detail_links[0].click()

    booking_page = PatientBookingPage(driver)
    booking_page.wait_page_loaded()
    slots = booking_page.get_available_slots()
    assert slots, "No available schedule slot is present for the guarded booking flow"
    slot_lines = [line.strip() for line in slots[0].text.splitlines() if line.strip()]
    assert len(slot_lines) >= 2, "Available schedule does not expose date and time text"

    booking_page.select_date(slot_lines[0])
    booking_page.select_time_slot(slot_lines[1])
    booking_page.submit_booking()
    booking_page.wait_booking_success()
