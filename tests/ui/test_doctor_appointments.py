"""Read-only UI checks for the doctor's appointment list."""

import pytest

from pages.doctor_appointments_page import DoctorAppointmentsPage


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_doctor_can_view_appointments(doctor_authenticated_driver):
    """A configured doctor can see appointment records or the explicit empty state."""
    appointments = DoctorAppointmentsPage(doctor_authenticated_driver)
    appointments.open_doctor_appointments()
    appointments.wait_for_route()
    appointments.wait_page_loaded()
    state = appointments.wait_for_list_state()

    assert state in {"records", "empty"}, f"Unexpected doctor appointment state: {state!r}"
    if state == "records":
        record = appointments.get_first_appointment()
        assert record is not None, "Appointment list reported records but no record was readable"
        assert record["patient"], "Doctor appointment record has no patient name"
        assert record["status"], "Doctor appointment record has no status"
    else:
        assert appointments.is_empty_state_visible(), "Doctor appointment empty state is not visible"


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_doctor_can_filter_completed_appointments(doctor_authenticated_driver):
    """The completed status filter shows only completed appointments or no matches."""
    appointments = DoctorAppointmentsPage(doctor_authenticated_driver)
    appointments.open_doctor_appointments()
    appointments.wait_for_route()
    appointments.wait_page_loaded()

    assert appointments.select_status_filter("已完成") == "已完成"
    state = appointments.wait_for_filtered_list_state("已就诊")
    assert state in {"records", "empty"}, f"Unexpected filtered appointment state: {state!r}"
    if state == "records":
        records = appointments.get_appointment_records()
        assert records, "Completed filter reported records but none were readable"
        assert all(record["status"] == "已就诊" for record in records), (
            "Completed filter returned a record with a different status"
        )


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_doctor_can_filter_pending_appointments(doctor_authenticated_driver):
    """The pending status filter shows only pending appointments or no matches."""
    appointments = DoctorAppointmentsPage(doctor_authenticated_driver)
    appointments.open_doctor_appointments()
    appointments.wait_for_route()
    appointments.wait_page_loaded()

    assert appointments.select_status_filter("待接诊") == "待接诊"
    state = appointments.wait_for_filtered_list_state("待就诊")
    assert state in {"records", "empty"}, f"Unexpected filtered appointment state: {state!r}"
    if state == "records":
        records = appointments.get_appointment_records()
        assert records, "Pending filter reported records but none were readable"
        assert all(record["status"] == "待就诊" for record in records), (
            "Pending filter returned a record with a different status"
        )
