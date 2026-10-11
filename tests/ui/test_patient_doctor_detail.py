"""Read-only UI checks for a patient doctor detail page."""

import pytest

from pages.patient_doctor_detail_page import PatientDoctorDetailPage
from pages.patient_doctor_page import PatientDoctorPage
from pages.patient_entry_page import PatientEntryPage


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_patient_can_view_doctor_detail(authenticated_driver):
    """A patient can open a doctor detail page without booking an appointment."""
    driver = authenticated_driver
    patient_entry = PatientEntryPage(driver)
    patient_entry.open_patient_portal()

    doctor_list = PatientDoctorPage(driver)
    doctor_list.open_doctor_search()
    doctor_list.wait_for_route()
    doctor_list.wait_for_heading()
    state = doctor_list.wait_for_list_state()
    assert state == "records", (
        "A doctor record is required to verify the doctor detail page"
    )

    detail_url = doctor_list.get_first_doctor_detail_url()
    assert detail_url, "Doctor detail link did not expose a destination URL"
    doctor_list.open_first_doctor_detail()

    detail_page = PatientDoctorDetailPage(driver)
    detail_page.wait_for_route()
    detail_page.wait_page_loaded()

    doctor_name = detail_page.get_doctor_name()
    assert doctor_name, "Doctor detail heading did not contain a doctor name"
    assert detail_page.is_detail_page_visible(), (
        "Doctor name, department, and specialty details are not all visible"
    )
    assert detail_page.is_booking_button_visible(), (
        "Doctor detail page does not show the confirmed booking button"
    )
