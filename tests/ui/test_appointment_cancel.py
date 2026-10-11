"""Guarded UI test for cancelling a pending patient appointment."""

import pytest

from pages.patient_appointment_cancel_page import PatientAppointmentCancelPage


@pytest.mark.ui
@pytest.mark.write
@pytest.mark.regression
def test_patient_can_cancel_pending_appointment(
    enable_write_test, authenticated_driver
):
    """Cancel one existing pending appointment and verify its displayed status."""
    appointments_page = PatientAppointmentCancelPage(authenticated_driver)
    appointments_page.open_appointments()
    appointments_page.wait_for_route()
    appointments_page.wait_for_heading()

    state = appointments_page.wait_for_list_state()
    if state == "empty":
        pytest.skip("没有可取消的预约")

    appointment_label = appointments_page.find_cancelable_appointment()
    if not appointment_label:
        pytest.skip("没有处于待就诊状态的可取消预约")

    appointments_page.cancel_appointment(appointment_label)
    status = appointments_page.wait_for_cancelled_status(appointment_label)
    assert status == "已取消", (
        f"Expected appointment status to be 已取消, got: {status!r}"
    )
