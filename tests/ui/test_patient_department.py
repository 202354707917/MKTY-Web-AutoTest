"""Read-only UI checks for the patient department selection page."""

import pytest

from pages.patient_department_page import PatientDepartmentPage


@pytest.mark.ui
@pytest.mark.readonly
@pytest.mark.regression
def test_patient_department_page_reaches_read_only_state(authenticated_driver):
    """The department page shows department choices or an explicit empty state."""
    departments_page = PatientDepartmentPage(authenticated_driver)
    departments_page.open_departments()
    departments_page.wait_for_route()
    departments_page.wait_page_loaded()

    state = departments_page.wait_for_list_state()
    assert state in {"records", "empty"}, (
        f"Unexpected department list state: {state!r}"
    )
    if state == "empty":
        assert departments_page.is_empty_state_visible(), (
            "Department list reported empty but the empty state is not visible"
        )
    else:
        names = departments_page.get_department_names()
        assert names, "Department list reported records but no department names were found"
