"""Read-only UI checks for a doctor's appointment detail view."""

import pytest

from pages.doctor_appointment_detail_page import DoctorAppointmentDetailPage
from pages.doctor_appointments_page import DoctorAppointmentsPage


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_doctor_can_view_appointment_detail(doctor_authenticated_driver):
    """A doctor can open one existing appointment's read-only detail view."""
    driver = doctor_authenticated_driver
    appointments = DoctorAppointmentsPage(driver)
    appointments.open_doctor_appointments()
    appointments.wait_for_route()
    appointments.wait_page_loaded()
    state = appointments.wait_for_list_state()
    if state == "empty":
        pytest.skip("当前医生没有可查看的预约记录")

    detail_url = appointments.get_first_appointment_detail_url()
    detail = DoctorAppointmentDetailPage(driver)
    detail.open_detail(detail_url)
    detail.wait_for_route()
    detail.wait_page_loaded()

    details = detail.get_appointment_details()
    assert details["title"] in {"书写电子病历", "病历详情"}, (
        "Doctor appointment detail title is not visible"
    )
    assert details["patient"], "Doctor appointment detail has no patient information"
    assert details["appointment_number"], (
        "Doctor appointment detail has no appointment number"
    )
    assert details["appointment_time"], (
        "Doctor appointment detail has no appointment date or time slot"
    )
    assert details["department"], "Doctor appointment detail has no department information"
    assert detail.is_detail_visible(), "Doctor appointment detail page is not visible"
