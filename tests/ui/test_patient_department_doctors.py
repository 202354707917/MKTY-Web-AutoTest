"""Read-only UI checks for doctors filtered by department."""

import pytest

from pages.patient_department_page import PatientDepartmentPage
from pages.patient_doctor_filter_page import PatientDoctorFilterPage


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_patient_can_view_doctors_by_department(authenticated_driver):
    """A patient can open the doctor list filtered by a department."""
    departments_page = PatientDepartmentPage(authenticated_driver)
    departments_page.open_departments()
    departments_page.wait_for_route()
    departments_page.wait_page_loaded()

    if departments_page.wait_for_list_state() == "empty":
        pytest.skip("没有可用于筛选医生的科室")

    filter_url = departments_page.get_first_department_filter_url()
    doctors_page = PatientDoctorFilterPage(authenticated_driver)
    doctors_page.open_filtered_doctors(filter_url)
    actual_url = doctors_page.wait_for_route()
    doctors_page.wait_page_loaded()

    assert "departmentId=" in actual_url, (
        "Filtered doctor route does not contain departmentId"
    )
    assert doctors_page.get_current_department(), (
        "Filtered doctor page does not show the selected department"
    )

    state = doctors_page.wait_for_list_state()
    assert state in {"records", "empty"}, (
        f"Unexpected filtered doctor list state: {state!r}"
    )
    if state == "records":
        assert doctors_page.get_doctor_count() > 0, (
            "Filtered doctor list reported records but no doctor names were found"
        )
    else:
        assert doctors_page.is_empty_state_visible(), (
            "Filtered doctor list reported empty but the empty state is not visible"
        )
